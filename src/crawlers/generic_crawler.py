"""
Generic Metadata-Driven Crawler Engine
Production-grade: Concurrent, Rate-Limited, Retry, Schema-Driven
"""
import os
import sys
import json
import yaml
import asyncio
import logging
import time
import random
import argparse
from bs4 import BeautifulSoup
from typing import Any, Dict, Optional, Set
from curl_cffi.requests import AsyncSession
from urllib.parse import urlparse, urlunparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crawlers.sink import KafkaSink
from config import KAFKA_TOPIC, SCHEMA_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_logger = logging.getLogger("generic-crawler")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


def _load_schema_defaults(schema_path: str) -> tuple:
    """Fix #5: Load Avro schema to auto-fill missing fields (Schema-Driven Mapping).
    Returns (defaults dict, required_string_fields set)
    """
    defaults = {}
    required_strings = set()  # Fields that MUST be a string (non-nullable)
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        for field in schema.get('fields', []):
            name = field['name']
            field_type = field.get('type')
            default = field.get('default')
            # Track non-nullable string fields (Avro will reject None)
            if field_type == 'string':
                required_strings.add(name)
            # Infer default if not explicitly set
            if default is not None:
                defaults[name] = default
            elif isinstance(field_type, dict) and field_type.get('type') == 'array':
                defaults[name] = []
            elif field_type == 'boolean' or (isinstance(field_type, list) and 'boolean' in field_type):
                defaults[name] = False
            elif field_type == 'long' or (isinstance(field_type, list) and 'long' in field_type):
                defaults[name] = 0
            else:
                defaults[name] = None
    except Exception as e:
        _logger.warning(f"Could not load schema defaults from {schema_path}: {e}")
    return defaults, required_strings


class GenericCrawler:
    def __init__(self, config_path: str, sink: KafkaSink, schema_path: str,
                 concurrency: int = 5):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.sink = sink
        # Fix #5: Load schema-driven defaults once at startup
        self.schema_defaults, self.required_strings = _load_schema_defaults(schema_path)
        # Fix #2: Semaphore for rate limiting
        self.semaphore = asyncio.Semaphore(concurrency)
        
        # Track seen IDs during this run to detect redundancy/loops
        self.seen_ids: Set[str] = set()
        # Track max items per page to detect significant drops (e.g. 45 -> 10)
        self.max_items_seen = 0
        self.small_page_series = 0

        # Support per-source custom headers from YAML config
        self.base_headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        # Merge any source-specific headers from YAML
        extra_headers = self.config.get('headers', {})
        self.base_headers.update(extra_headers)

        # impersonate target: allow per-source override in YAML (default: chrome120)
        self.impersonate = self.config.get('impersonate', 'chrome120')

    async def fetch_page(self, session: AsyncSession, url: str) -> str:
        """Fix #4: Retry with exponential backoff. Fix #2: Rate-limited via semaphore.
        Uses curl_cffi to impersonate Chrome TLS fingerprint — bypasses bot detection.
        """
        for attempt in range(3):
            try:
                async with self.semaphore:
                    # Fix #7: Random jitter delay
                    await asyncio.sleep(random.uniform(0.5, 2.0))
                    _logger.info(f"Fetching (attempt {attempt + 1}): {url}")
                    response = await session.get(url, headers=self.base_headers, timeout=30)
                    response.raise_for_status()
                    return response.text
            except Exception as e:
                _logger.warning(f"Retry {attempt + 1}/3 failed for {url}: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # Backoff: 1s, 2s
        raise Exception(f"Failed to fetch after 3 attempts: {url}")

    def _clean_url(self, url: str) -> str:
        """Strip query parameters and fragments using simple string splitting for speed and reliability."""
        if not url:
            return ""
        # Remove query params and fragments, then strip trailing slashes
        return url.split('?')[0].split('#')[0].rstrip('/')

    def parse_item(self, container: BeautifulSoup) -> Dict[str, Any]:
        """Parse a single job card using YAML field definitions."""
        # Start with schema defaults (Fix #5)
        data = dict(self.schema_defaults)

        for field_name, rules in self.config['fields'].items():
            selector = rules.get('selector')
            attr = rules.get('attribute', 'text')

            element = container.select_one(selector) if selector else container

            if not element:
                if attr == 'exists':
                    data[field_name] = False
                # Else: keep schema default
                continue

            if attr == 'text':
                data[field_name] = element.get_text(strip=True) or data.get(field_name)
            elif attr == 'exists':
                data[field_name] = True
            elif attr in ('href', 'src', 'data-job-id'):
                val = element.get(attr)
                if val and attr == 'href' and val.startswith('/'):
                    val = self.config['base_url'] + val
                data[field_name] = val
            else:
                data[field_name] = element.get(attr)

        # Fix #3: Ensure job_id is never None and is clean
        if not data.get('job_id'):
            data['job_id'] = data.get('url') or f"{self.config['name']}_{int(time.time())}_{random.randint(1000,9999)}"
        
        # Clean job_id if it's a URL (fixes TopDev tracking params issue)
        if isinstance(data['job_id'], str) and data['job_id'].startswith('http'):
            data['job_id'] = self._clean_url(data['job_id'])

        # Fix TopDev TypeError: coerce None → "" for non-nullable Avro string fields
        for field_name in self.required_strings:
            if data.get(field_name) is None:
                data[field_name] = ""

        return data

    async def fetch_and_parse(self, session: AsyncSession, url: str) -> tuple[int, str, int]:
        """Fetch one page, parse all items, emit to Kafka.
        Returns (count of items found, fingerprint of data, new_items_count).
        """
        try:
            html = await self.fetch_page(session, url)
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.select(self.config['container_selector'])
            _logger.info(f"Found {len(items)} items on {url}")

            current_job_ids = []
            new_items_count = 0
            for item in items:
                job_data = self.parse_item(item)
                # Fix #3: Fallback key from url if job_id still missing
                key = job_data.get('job_id') or job_data.get('url')
                jid = str(key)
                current_job_ids.append(jid)
                
                if jid not in self.seen_ids:
                    new_items_count += 1
                    self.seen_ids.add(jid)
                
                self.sink.emit(job_data, key=key)
            
            # Create a fingerprint from sorted job IDs
            fingerprint = "|".join(sorted(current_job_ids)) if current_job_ids else "EMPTY"
            return len(items), fingerprint, new_items_count
        except Exception as e:
            _logger.error(f"Error processing {url}: {e}")
            return 0, "ERROR", 0

    async def run(self, max_pages: int = 1):
        """Concurrent page crawling with batching.
        Stops if:
        1. A batch yields 0 items.
        2. 3 consecutive pages have identical data (infinite loop protection).
        """
        effective_limit = max_pages if max_pages > 0 else 9999
        batch_size = 5
        
        async with AsyncSession(impersonate=self.impersonate) as session:
            try:
                current_page = 1
                last_fingerprint = None
                consecutive_duplicates = 0
                
                while current_page <= effective_limit:
                    batch_end = min(current_page + batch_size, effective_limit + 1)
                    tasks = []
                    for p in range(current_page, batch_end):
                        url = self.config['list_url_template'].format(page=p)
                        tasks.append(self.fetch_and_parse(session, url))
                    
                    _logger.info(f"Starting batch crawl: pages {current_page} to {batch_end-1} for source={self.config['name']}")
                    batch_results = await asyncio.gather(*tasks)
                    
                    # Process results in order to check for consecutive duplicates/redundancy
                    stop_crawling = False
                    for count, fingerprint, new_count in batch_results:
                        if count == 0:
                            stop_crawling = True
                            _logger.info(f"Found empty page. Stopping.")
                            break
                        
                        # Check for redundancy (e.g. site returning same "suggested" jobs)
                        # If more than 50% of items are already seen, we likely reached the end
                        redundancy = 1.0 - (new_count / count) if count > 0 else 1.0
                        
                        if redundancy > 0.5:
                            _logger.info(f"High redundancy detected ({redundancy:.1%}). Likely reached 'Suggested Jobs' or end of results. Stopping.")
                            stop_crawling = True
                            break
                        
                        # Detect significant count drop (e.g. from 45 results to 10 suggestions)
                        if count > self.max_items_seen:
                            self.max_items_seen = count
                        
                        # If current count is <= 50% of max seen AND we've seen enough items to have a baseline
                        if self.max_items_seen >= 15 and count <= self.max_items_seen * 0.6:
                            self.small_page_series += 1
                            _logger.warning(f"Detected small page ({count} items vs max {self.max_items_seen}). Series: {self.small_page_series}")
                        else:
                            self.small_page_series = 0

                        if self.small_page_series >= 2:
                            _logger.info("Significant count drop detected for 2 consecutive pages. Stopping.")
                            stop_crawling = True
                            break

                        if new_count == 0 and count > 0:
                            _logger.info(f"Page contains no new items. Stopping.")
                            stop_crawling = True
                            break

                        if fingerprint == last_fingerprint and fingerprint != "EMPTY":
                            consecutive_duplicates += 1
                            _logger.warning(f"Detected identical page data (Consecutive: {consecutive_duplicates})")
                        else:
                            consecutive_duplicates = 0
                        
                        last_fingerprint = fingerprint
                        
                        if consecutive_duplicates >= 2: # 2 duplicates = 3 identical pages total
                            _logger.info(f"Detected 3 consecutive pages with same data. Stopping.")
                            stop_crawling = True
                            break
                    
                    if stop_crawling:
                        break
                    
                    current_page += batch_size
                    # Jitter between batches
                    await asyncio.sleep(random.uniform(1.0, 3.0))

                _logger.info(f"Completed crawl for source={self.config['name']}")
            finally:
                self.sink.flush()


async def main():
    parser = argparse.ArgumentParser(description='Generic Metadata-Driven Crawler (Production-Grade)')
    parser.add_argument('--config', required=True, help='Path to YAML config file')
    parser.add_argument('--max-pages', type=int, default=1, help='Max pages to crawl')
    parser.add_argument('--concurrency', type=int, default=5, help='Max concurrent requests')
    args = parser.parse_args()

    sink = KafkaSink(topic=KAFKA_TOPIC, schema_path=SCHEMA_PATH)
    crawler = GenericCrawler(
        config_path=args.config,
        sink=sink,
        schema_path=SCHEMA_PATH,
        concurrency=args.concurrency
    )

    try:
        await crawler.run(max_pages=args.max_pages)
    finally:
        sink.close()


if __name__ == "__main__":
    asyncio.run(main())

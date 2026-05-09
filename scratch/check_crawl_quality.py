
import asyncio
import yaml
import json
import os
import sys
from typing import List, Dict, Any

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)

# Import from src
from src.crawlers.generic_crawler import GenericCrawler

class MockSink:
    def __init__(self):
        self.data = []
    def emit(self, record: Dict[str, Any], key: str = None):
        self.data.append(record)
    def flush(self): pass
    def close(self): pass

async def check_quality(source_name: str, pages: int = 2):
    print(f"--- Checking Quality for {source_name} (Pages: {pages}) ---")
    config_path = f"configs/crawlers/{source_name}.yaml"
    schema_path = "schemas/raw/job_listing.avsc"
    
    sink = MockSink()
    crawler = GenericCrawler(config_path, sink, schema_path, concurrency=2)
    
    # Run the crawl
    await crawler.run(max_pages=pages)
    
    print(f"Captured {len(sink.data)} items for {source_name}")
    
    if sink.data:
        # Check first 2 items for errors
        for i, item in enumerate(sink.data[:2]):
            print(f"\nItem {i+1} Sample:")
            fields_to_show = ['job_id', 'title', 'company', 'salary', 'location', 'experience']
            for f in fields_to_show:
                print(f"  {f}: {item.get(f)}")
    
    return sink.data

async def main():
    sources = ["topdev", "topcv"]
    for source in sources:
        await check_quality(source, pages=2)

if __name__ == "__main__":
    asyncio.run(main())

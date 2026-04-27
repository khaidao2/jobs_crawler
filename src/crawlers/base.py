"""Base class for all job crawlers."""

from __future__ import annotations
import abc
import logging
from typing import Any
from curl_cffi.requests import AsyncSession

class BaseCrawler(abc.ABC):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.logger = logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    def page_url(self, slug: str, page: int) -> str:
        """Construct the URL for a listing page."""
        pass

    @abc.abstractmethod
    def parse_listing(self, html: str, **kwargs) -> list[dict[str, Any]]:
        """Parse the listing page HTML into a list of job card dictionaries."""
        pass

    @abc.abstractmethod
    def parse_detail(self, html: str, **kwargs) -> dict[str, Any]:
        """Parse the detail page HTML into a dictionary of extra fields."""
        pass

    def merge_enrichments(self, card: dict[str, Any], extras: dict[str, Any]) -> dict[str, Any]:
        """Card fields win; enrichment only fills empty slots."""
        merged = dict(card)
        for k, v in extras.items():
            if v is None or v == "" or v == []:
                continue
            if merged.get(k) in (None, "", [], 0):
                merged[k] = v
        return merged

    @staticmethod
    def normalize_string(t: str | None) -> str | None:
        if not t:
            return None
        cleaned = t.replace("\r", "").replace("\xa0", " ").strip()
        cleaned = " ".join(cleaned.split())
        return cleaned if cleaned else None

    @staticmethod
    def safe_text(el: Any) -> str | None:
        if el is None:
            return None
        t = el.get_text(separator=" ", strip=True)
        return t or None

    async def fetch_detail_and_merge(self, session: AsyncSession, job_dict: dict[str, Any]) -> dict[str, Any]:
        url = job_dict.get("url")
        if not url:
            return job_dict
        try:
            res = await session.get(url)
            extras = self.parse_detail(res.text)
            return self.merge_enrichments(job_dict, extras)
        except Exception as e:
            self.logger.error(f"Error fetching detail {url}: {e}")
            return job_dict

    async def fetch_listing(self, session: AsyncSession, slug: str, page: int, **kwargs) -> list[dict[str, Any]]:
        url = self.page_url(slug, page)
        try:
            res = await session.get(url)
            return self.parse_listing(res.text, page_number=page, **kwargs)
        except Exception as e:
            self.logger.error(f"Error fetching listing {url}: {e}")
            return []

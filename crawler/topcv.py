"""Pure parse functions for TopCV (topcv.vn)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from bs4 import BeautifulSoup

_BASE_URL = "https://www.topcv.vn"

DEFAULT_CATEGORIES: list[dict[str, str]] = [
    {"slug": "tim-viec-lam-cong-nghe-thong-tin-cr257", "label": "Việc làm Công nghệ thông tin"},
]

_CARD_SEL = "div.job-item-search-result"


def page_url(slug: str, page: int) -> str:
    sep = "&" if "?" in slug else "?"
    return f"{_BASE_URL}/{slug}" if page == 1 else f"{_BASE_URL}/{slug}{sep}page={page}"

def _safe_text(el: Any) -> str | None:
    if el is None:
        return None
    t = el.get_text(separator=" ", strip=True)
    return t or None

def _normalize_string(t: str | None) -> str | None:
    if not t:
        return None
    cleaned = t.replace("\r", "").replace("\xa0", " ").strip()
    cleaned = " ".join(cleaned.split())
    return cleaned if cleaned else None

def _clean_detail_html(content_div: Any) -> str | None:
    if not content_div:
        return None
    # Use newline separator to preserve vertical bullet points
    text = content_div.get_text(separator="\n", strip=True)
    # Clean whitespace aggressively per line
    lines = [ " ".join(line.replace("\xa0", " ").replace("\r", " ").split()) for line in text.split("\n") ]
    cleaned = "\n".join([line for line in lines if line])
    return cleaned if cleaned else None

def _parse_card(card: Any, category: str, page_number: int, crawled_at: int) -> dict[str, Any] | None:
    job_id = card.get("data-job-id", "").strip()
    if not job_id:
        return None
        
    title_block = card.find("div", class_="title-block")
    title_tag = title_block.find("h3", class_="title").find("a") if title_block else None
    
    title = ""
    if title_tag:
        span_tag = title_tag.find("span")
        if span_tag:
            title = span_tag.text.strip()
        if not title:
            title = title_tag.get("title", "")
            
    url = title_tag.get("href") if title_tag else None
    if url and url.startswith("//"):
        url = "https:" + url
    elif url and url.startswith("/"):
        url = _BASE_URL + url
        
    company_tag = title_block.find("a", class_="company") if title_block else None
    company = ""
    if company_tag:
        comp_span = company_tag.find("span", class_="company-name")
        company = comp_span.text.strip() if comp_span else company_tag.text.strip()
    company_url = company_tag.get("href") if company_tag else None
    
    avatar_div = card.find("div", class_="avatar")
    logo_tag = avatar_div.find("img") if avatar_div else None
    logo_url = logo_tag.get("data-src") or logo_tag.get("src") if logo_tag else None
    
    salary_tag = card.find("label", class_="title-salary") or card.find("label", class_="salary")
    salary = salary_tag.text.strip() if salary_tag else None
    
    location_tag = card.find("label", class_="address")
    location = None
    if location_tag:
        loc_span = location_tag.find("span", class_="city-text")
        location = loc_span.text.strip() if loc_span else location_tag.text.strip()
        
    experience_tag = card.find("label", class_="exp")
    experience = experience_tag.text.strip() if experience_tag else None
    
    tags = []
    tag_container = card.find("div", class_="tag")
    if tag_container:
        for t in tag_container.find_all(["a", "span"], class_="item-tag"):
            t_txt = t.text.strip()
            if t_txt:
                tags.append(" ".join(t_txt.split()))
                
    updated_at = None
    posted_at = None
    icon_div = card.find("div", class_="icon")
    if icon_div:
        update_label = icon_div.find("label", class_="label-update")
        if update_label:
            updated_at = update_label.get("data-original-title") or update_label.get("title", "")
            hidden_span = update_label.find("span", class_="hidden-on-quick-view")
            if hidden_span and hidden_span.next_sibling:
                node = hidden_span.next_sibling
                p_text = node.text.strip() if hasattr(node, "text") else str(node).strip()
                if p_text:
                    posted_at = p_text

    is_urgent = bool(card.find("label", class_="is-urgent"))
    is_highlight = bool(card.find("label", class_="tag-highlight-label"))
    is_flash = "bg-flash-job" in card.get("class", []) or bool(card.find("div", class_="tag-job-flash"))
    company_verified = bool(card.find("span", class_="icon-verified-employer"))

    return {
        "job_id": _normalize_string(job_id),
        "title": _normalize_string(title),
        "company": _normalize_string(company),
        "url": url.strip() if url else None,
        "company_url": company_url.strip() if company_url else None,
        "logo_url": logo_url.strip() if logo_url else None,
        "salary": _normalize_string(salary),
        "location": _normalize_string(location),
        "experience": _normalize_string(experience),
        "tags": tags,
        "updated_at": _normalize_string(updated_at),
        "posted_at": _normalize_string(posted_at),
        "is_urgent": is_urgent,
        "is_highlight": is_highlight,
        "is_flash": is_flash,
        "company_verified": company_verified,
        "category": category,
        "page_number": page_number,
        "crawled_at": crawled_at,
        "job_description": None,
        "job_requirement": None,
        "job_benefit": None,
        "deadline": None,
        "working_times": []
    }

def parse_listing(
    html: str, *, category: str, page_number: int, crawled_at: int
) -> list[dict[str, Any]]:
    # Fallback to html.parser if lxml isn't installed yet
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
        
    cards = soup.select(_CARD_SEL)
    records: list[dict[str, Any]] = []
    for card in cards:
        rec = _parse_card(card, category, page_number, crawled_at)
        if rec is not None:
            records.append(rec)
    return records

def parse_detail_enrichments(html: str) -> dict[str, Any]:
    """Extract fields that don't appear on the listing card."""
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
        
    out: dict[str, Any] = {
        "job_description": None,
        "job_requirement": None,
        "job_benefit": None,
        "deadline": None,
        "working_times": []
    }

    deadline_elem = soup.find("div", class_="job-detail__info--deadline-date")
    if deadline_elem:
        d = deadline_elem.get_text(separator=" ", strip=True)
        out["deadline"] = _normalize_string(d)
            
    desc_items = soup.find_all("div", class_="job-description__item")
    for item in desc_items:
        h3 = item.find("h3")
        if not h3:
            continue
        title = h3.get_text(separator=" ", strip=True).lower()
        content_div = item.find("div", class_="job-description__item--content")
        
        cleaned_text = _clean_detail_html(content_div)
        
        if "mô tả công việc" in title:
            out["job_description"] = cleaned_text
        elif "yêu cầu ứng viên" in title:
            out["job_requirement"] = cleaned_text
        elif "quyền lợi" in title:
            out["job_benefit"] = cleaned_text
            
    return out

def merge_enrichments(card: dict[str, Any], extras: dict[str, Any]) -> dict[str, Any]:
    """Card fields win; enrichment only fills empty slots."""
    merged = dict(card)
    for k, v in extras.items():
        if v is None or v == "" or v == []:
            continue
        if merged.get(k) in (None, "", [], 0):
            merged[k] = v
    return merged

def resolve_categories(override: str | None) -> list[dict[str, str]]:
    raw = override or ""
    if not raw:
        return list(DEFAULT_CATEGORIES)
    slug_to_label = {c["slug"]: c["label"] for c in DEFAULT_CATEGORIES}
    return [
        {"slug": s.strip(), "label": slug_to_label.get(s.strip(), s.strip())}
        for s in raw.split(",") if s.strip()
    ]


if __name__ == "__main__":
    import asyncio
    import json
    import os
    import time
    import pandas as pd
    from curl_cffi.requests import AsyncSession

    async def run_async_test():
        print("Starting Async Test Crawl for TopCV...")
        base_url = "tim-viec-lam-cong-nghe-thong-tin-cr257?type_keyword=1&category_family=r257&saturday_status=0"
        crawled_at = int(time.time())
        
        async with AsyncSession(impersonate="chrome120") as session:
            # 1. Fetch Page 1
            print("Fetching Page 1...")
            res = await session.get(page_url(base_url, 1))
            jobs = parse_listing(res.text, category="it", page_number=1, crawled_at=crawled_at)
            print(f"Found {len(jobs)} jobs. Fetching details concurrently...")
            
            # 2. Fetch Details Concurrently
            async def fetch_detail_and_merge(job_dict):
                url = job_dict.get("url")
                if not url: return job_dict
                try:
                    dt_res = await session.get(url)
                    extras = parse_detail_enrichments(dt_res.text)
                    return merge_enrichments(job_dict, extras)
                except Exception as e:
                    print(f"Error fetching {url}: {e}")
                    return job_dict

            tasks = [fetch_detail_and_merge(j) for j in jobs]
            final_jobs = await asyncio.gather(*tasks)

        if final_jobs:
            print("\n" + "="*50)
            print("SAMPLE JOB EXTRACTED:")
            print("="*50)
            print(json.dumps(final_jobs[0], indent=2, ensure_ascii=False))
            print("="*50 + "\n")
            
            # Save parquet
            out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../topcv_jobs.parquet"))
            df = pd.DataFrame(final_jobs)
            df.to_parquet(out_path, index=False)
            print(f"Successfully saved {len(final_jobs)} jobs to {out_path} at lightning speed!")

    asyncio.run(run_async_test())

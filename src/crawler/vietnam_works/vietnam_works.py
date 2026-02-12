import requests
import time
import hashlib
import uuid
import json
from typing import List, Dict, Optional
from src.utils.utils import save_to_csv
import pandas as pd

class VNWorksCrawler:
    API_URL = "https://ms.vietnamworks.com/job-search/v1.0/search"

    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "x-api-key": "vietnamworks",
        "x-device-id": "crawl-script",
    }

    def __init__(self, hits_per_page: int = 50, sleep_time: float = 0.8):
        self.hits_per_page = hits_per_page
        self.sleep_time = sleep_time

    # =========================
    # PAYLOAD
    # =========================
    def build_payload(self, page: int) -> Dict:
        return {
            "userId": 0,
            "query": "",
            "page": page,
            "hitsPerPage": self.hits_per_page,
            "retrieveFields": [
                "jobId", "jobTitle", "jobUrl", "companyName", "companyLogo",
                "approvedOn", "expiredOn",
                "salary", "salaryMin", "salaryMax", "prettySalary",
                "isSalaryVisible", "salaryCurrency", "salaryPeriodId",
                "jobLevel", "jobLevelVI",
                "workingLocations", "address",
                "skills", "benefits",
                "jobDescription", "jobRequirement",
                "industriesV3", "jobFunctionsV3",
            ],
            "filter": [
                {
                    "field": "jobFunction",
                    "value": '[{"parentId":5,"childrenIds":[-1]}]',
                }
            ],
        }

    # =========================
    # HASH ID
    # =========================
    def make_hash_id(
        self,
        job_url: str,
        job_title: str = "",
        company: str = "",
    ) -> str:
        if job_url:
            return hashlib.md5(job_url.encode("utf-8")).hexdigest()

        parts = [
            f"title_{job_title[:50].lower()}",
            f"company_{company[:30].lower()}",
        ]
        return hashlib.md5("_".join(parts).encode("utf-8")).hexdigest()

    # =========================
    # CLEAN HTML
    # =========================
    @staticmethod
    def clean_html(text: Optional[str]) -> str:
        if not text:
            return ""
        import re
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # =========================
    # NORMALIZE
    # =========================
    def normalize_job(self, raw: Dict, page: int, index: int) -> Dict:
        ts = f"{page}_{index}_{time.time()}"

        return {
            "_id": self.make_hash_id(
                raw.get("jobUrl", ""),
                raw.get("jobTitle", ""),
                raw.get("companyName", ""),
            ),
            "job_id": raw.get("jobId"),
            "title": raw.get("jobTitle", ""),
            "company": raw.get("companyName", ""),
            "company_logo": raw.get("companyLogo", ""),
            "job_url": raw.get("jobUrl", ""),
            "salary": raw.get("salary"),
            "salary_min": raw.get("salaryMin"),
            "salary_max": raw.get("salaryMax"),
            "pretty_salary": raw.get("prettySalary", ""),
            "salary_visible": raw.get("isSalaryVisible", False),
            "job_level": raw.get("jobLevel"),
            "job_level_vi": raw.get("jobLevelVI"),
            "locations": [
                l.get("cityNameVI") or l.get("cityName")
                for l in (raw.get("workingLocations") or [])
                if l
            ],
            "skills": [s.get("skillName") for s in raw.get("skills") or [] if s],
            "benefits": [
                b.get("benefitNameVI") or b.get("benefitName")
                for b in raw.get("benefits") or []
                if b
            ],
            "job_description": self.clean_html(raw.get("jobDescription")),
            "job_requirement": self.clean_html(raw.get("jobRequirement")),
            "crawl_page": page,
            "crawl_index": index,
            "crawl_ts": ts,
        }

    # =========================
    # CRAWL
    # =========================
    def crawl_all_jobs(self) -> List[Dict]:
        page = 1
        jobs = []
        total_pages = None

        while True:
            print(f"Crawling page {page}")
            resp = requests.post(
                self.API_URL,
                json=self.build_payload(page),
                headers=self.HEADERS,
                timeout=30,
            )

            if resp.status_code != 200:
                print("HTTP Error", resp.status_code)
                break

            data = resp.json()
            meta = data.get("meta", {})

            if total_pages is None:
                total_pages = meta.get("nbPages", 0)
                print(f"Total pages: {total_pages}")

            hits = data.get("data") or []
            if not hits:
                break

            for idx, raw in enumerate(hits):
                jobs.append(self.normalize_job(raw, page, idx))

            if page >= total_pages:
                break

            page += 1
            time.sleep(self.sleep_time)

        return jobs

    # =========================
    # DEDUP
    # =========================
    @staticmethod
    def deduplicate_jobs(jobs: List[Dict]):
        seen = set()
        unique, dup = [], []

        for j in jobs:
            if j["job_id"] in seen:
                dup.append(j)
            else:
                seen.add(j["job_id"])
                unique.append(j)

        return unique, dup

    # =========================
    # STATS
    # =========================
    @staticmethod
    def print_stats(jobs: List[Dict], title="STATS"):
        print("\n" + "=" * 40)
        print(title)
        print("=" * 40)
        print("Total jobs:", len(jobs))

    # =========================
    # RUN PIPELINE
    # =========================
    def run(self):
        print("VietnamWorks IT Crawler")
        raw_jobs = self.crawl_all_jobs()

        unique, dup = self.deduplicate_jobs(raw_jobs)
        save_to_csv(unique, "vietnamworks.csv", datasource="vietnamworks")

        print(f"Unique: {len(unique)} | Duplicate: {len(dup)}")

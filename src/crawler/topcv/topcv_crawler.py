import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
import logging
import random
import hashlib
from src.utils.utils import save_to_csv 

class TopCVCrawler:
    
    # ================= CONFIG =================
    SOURCE = "topcv"
    BASE_URL = "https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin-cr257"
    DETAIL_API = "https://www.topcv.vn/job-view-detail"

    MAX_PAGE = 1
    SLEEP_PAGE = (2, 4)
    SLEEP_DETAIL = (0.5, 1.5)

    HEADERS_HTML = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        "Referer": "https://www.topcv.vn/",
    }

    HEADERS_API = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.topcv.vn/",
    }
    # ================= INIT =================
    def __init__(self, db):
        self.db = db

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger("topcv")
    def parse_active_date(self, text: str) -> datetime | None:
        """
        Convert:
        - '7 ngày trước'
        - '2 tuần trước'
        - 'Hôm nay'
        - 'Hôm qua'
        → datetime UTC
        """
        if not text:
            return None

        text = text.lower().strip()
        now = datetime.now(timezone.utc)

        if "hôm nay" in text:
            return now

        if "hôm qua" in text:
            return now - timedelta(days=1)

        m = re.search(r"(\d+)\s*(ngày|tuần)", text)
        if not m:
            return None

        value = int(m.group(1))
        unit = m.group(2)

        if unit == "ngày":
            return now - timedelta(days=value)

        if unit == "tuần":
            return now - timedelta(days=value * 7)

        return None

    # ================= HASH ID =================
    def make_hash_id(self, raw_job_id: str) -> str:
        key = f"{self.SOURCE}_{raw_job_id}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    # ================= UTILS =================
    def safe_text(self, parent, selector):
        el = parent.select_one(selector)
        return el.get_text(strip=True) if el else None

    def safe_attr(self, parent, selector, attr):
        el = parent.select_one(selector)
        return el.get(attr) if el else None

    # ================= VERIFY =================
    # def verify_jobs(self, jobs):
    #     """
    #     Verify bằng hash_job_id giống VietnamWorks
    #     """
    #     verified = []
    #     for job in jobs:
    #         if not self.db.check_job_exists(job["hash_job_id"]):
    #             verified.append(job)
    #     return verified

    # ================= DETAIL API =================
    def fetch_job_detail(self, job_id: str) -> dict:
        try:
            api_url = f"{self.DETAIL_API}?id={job_id}"
            self.logger.info(f"[DETAIL_API] GET {api_url}")

            resp = requests.get(api_url, headers=self.HEADERS_API, timeout=15)
            resp.raise_for_status()

            html = resp.json().get("data", {}).get("html_job_detail")
            if not html:
                return {}

            soup = BeautifulSoup(html, "html.parser")

            def get_section(title):
                h3 = soup.find("h3", string=lambda t: t and title in t)
                if not h3:
                    return None
                box = h3.find_next_sibling("div", class_="content-tab")
                if not box:
                    return None
                ps = box.find_all("p")
                if ps:
                    return "\n".join(
                        p.get_text(strip=True)
                        for p in ps
                        if p.get_text(strip=True)
                    )
                return box.get_text(separator="\n", strip=True)

            header_items = soup.select(
                ".box-info-header .box-item-header .box-item-value"
            )

            return {
                "job_title_detail": self.safe_text(soup, ".box-title h2.title"),
                "job_description": get_section("Mô tả công việc"),
                "job_requirement": get_section("Yêu cầu ứng viên"),
                "job_benefit": get_section("Quyền lợi"),
                "job_detail_url": self.safe_attr(
                    soup, ".box-link-redirect a", "href"
                ),
                "salary_detail": header_items[0].get_text(strip=True)
                if len(header_items) > 0 else None,
                "location_detail": header_items[1].get_text(strip=True)
                if len(header_items) > 1 else None,
                "experience_detail": header_items[2].get_text(strip=True)
                if len(header_items) > 2 else None,
            }

        except Exception as e:
            self.logger.error(
                f"[DETAIL_API] ERROR job_id={job_id} err={e}"
            )
            return {}

    # ================= LIST PAGE =================
    def crawl_page(self, page: int):
        self.logger.info(f"[LIST] Start page={page}")

        resp = requests.get(
            self.BASE_URL,
            headers=self.HEADERS_HTML,
            params={"category_family": "r257", "page": page},
            timeout=15
        )

        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = soup.select("div.job-item-search-result")
        if not jobs:
            return None

        rows = []

        for idx, job in enumerate(jobs, 1):
            raw_job_id = job.get("data-job-id")
            if not raw_job_id:
                continue

            hash_job_id = self.make_hash_id(raw_job_id)

            # ===== ONLY ADD THIS BLOCK =====
            active_text = self.safe_text(job, ".job-item-body .time")
            active_date = self.parse_active_date(active_text)

            base = {
                "source": self.SOURCE,
                "job_id_raw": raw_job_id,
                "hash_job_id": hash_job_id,

                "job_title": self.safe_text(job, "h3.title a span"),
                "job_url": self.safe_attr(job, "h3.title a", "href"),
                "company_name": self.safe_text(job, ".company-name"),
                "salary": self.safe_text(job, ".title-salary"),
                "location": self.safe_text(job, ".address .city-text"),

                # ===== ONLY ADD THESE FIELDS =====
                "active_date": active_date.isoformat() if active_date else None,
                "active_date_raw": active_text,

                "page": page,
                "crawl_time": datetime.now(timezone.utc).isoformat(),
            }

            self.logger.info(
                f"[LIST] Detail {idx}/{len(jobs)} job_id={raw_job_id}"
            )

            detail = self.fetch_job_detail(raw_job_id)
            time.sleep(random.uniform(*self.SLEEP_DETAIL))

            rows.append({**base, **detail})

        return rows

    # ================= PIPELINE =================
    def crawl(self):
        all_rows = []
        page = 1

        while True:
            self.logger.info(
                f"========== START PAGE {page}/{self.MAX_PAGE} =========="
            )

            data = self.crawl_page(page)
            if not data:
                break

            before = len(data)
            data = data
            after = len(data)

            self.logger.info(
                f"[VERIFY] Page {page}: {before} → {after}"
            )

            all_rows.extend(data)

            if page >= self.MAX_PAGE:
                break

            time.sleep(random.uniform(*self.SLEEP_PAGE))
            page += 1

        return pd.DataFrame(all_rows)
    def run(self):
        self.logger.info("TopCV IT Crawler Started")

        df = self.crawl()
        self.logger.info(f"Total new jobs crawled: {len(df)}")
        if not df.empty:
            save_to_csv(df.to_dict(orient="records"), "topcv.csv", datasource="topcv")
        self.logger.info("TopCV IT Crawler Finished")

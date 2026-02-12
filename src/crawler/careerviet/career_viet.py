import requests
import logging
from datetime import datetime, timezone
from typing import List, Dict
from bs4 import BeautifulSoup

# 🔴 IMPORT HÀM CÓ SẴN – KHÔNG VIẾT LẠI
from src.utils.utils import save_to_csv


class CareerViet:
    SOURCE = "careerviet"

    HOME_URL = "https://careerviet.vn/"
    SEARCH_URL = "https://careerviet.vn/search-jobs"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/144.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://careerviet.vn",
        "Referer": "https://careerviet.vn/viec-lam/cntt-phan-mem-c1-vi.html",
    }

    def __init__(self, max_page_safe: int = 200):
        self.max_page_safe = max_page_safe
        self.session = requests.Session()
        self.now_utc = datetime.now(timezone.utc)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

        # INIT COOKIE
        r = self.session.get(
            self.HOME_URL,
            headers={"User-Agent": self.HEADERS["User-Agent"]},
            timeout=30,
        )
        r.raise_for_status()

        logging.info("INIT COOKIES: %s", self.session.cookies.get_dict())
        logging.info("=" * 80)

    # ================= FETCH LIST =================
    def fetch_page(self, page: int) -> Dict:
        payload = {
            "page": page,
            "LIMIT": 50,
            "SEARCH": 1,
            "OWNER": "kiemviec",
            "SORT": "dv",
            "v": "v0.2.1",

            # 🔴 FILTER CNTT
            "dataOne": 'a:1:{s:8:"INDUSTRY";s:1:"1";}',
            "dataTwo": 'a:0:{}',
        }

        resp = self.session.post(
            self.SEARCH_URL,
            headers=self.HEADERS,
            data=payload,
            timeout=30,
        )

        resp.raise_for_status()

        if "application/json" not in resp.headers.get("Content-Type", ""):
            logging.error("NOT JSON RESPONSE")
            return {"data": []}

        return resp.json()

    # ================= PARSE LIST =================
    def parse_jobs(self, resp_json: Dict) -> List[Dict]:
        jobs = []

        for item in resp_json.get("data", []):
            jobs.append(
                {
                    # ===== META =====
                    "source": self.SOURCE,
                    "crawl_time": self.now_utc.isoformat(),

                    # ===== JOB =====
                    "job_id": item.get("JOB_ID"),
                    "job_title": item.get("JOB_TITLE"),
                    "job_url": item.get("LINK_JOB"),
                    "job_active_date": item.get("JOB_ACTIVEDATE"),
                    "job_expire_date": item.get("JOB_LASTDATE"),
                    "job_salary_text": item.get("JOB_SALARY_STRING"),
                    "salary_from": item.get("JOB_FROMSALARY_CVR"),
                    "salary_to": item.get("JOB_TOSALARY_CVR"),

                    # ===== COMPANY =====
                    "company_name": item.get("EMP_NAME"),
                    "company_url": item.get("URL_EMP_DEFAULT"),
                    "company_logo": item.get("URL_LOGO_EMP"),

                    # ===== LOCATION =====
                    "locations": ", ".join(item.get("LOCATION_NAME_ARR", [])),

                    # ===== BENEFIT / TAG =====
                    "benefits_api": item.get("BENEFIT_NAME"),
                    "industries_api": item.get("TOP_INDUSTRY"),
                }
            )

        return jobs

    # ================= PARSE DETAIL =================
    def parse_job_detail(self, html: str) -> Dict:
        soup = BeautifulSoup(html, "html.parser")
        data = {}

        # ===== LOCATION =====
        loc = soup.select_one("section.job-detail-content .map p a")
        data["location_detail"] = loc.get_text(strip=True) if loc else None

        # ===== DETAIL BOX =====
        boxes = soup.select("section.job-detail-content .detail-box")

        if len(boxes) >= 2:
            items = boxes[1].select("li")
            data["updated_date"] = self.safe_p(items, 0)
            data["industries_detail"] = [a.get_text(strip=True) for a in items[1].select("a")] if len(items) > 1 else []
            data["job_type"] = self.safe_p(items, 2)

        if len(boxes) >= 3:
            items = boxes[2].select("li")
            data["salary_detail"] = self.safe_p(items, 0)
            data["experience"] = self.safe_p(items, 1)
            data["level"] = self.safe_p(items, 2)
            data["expire_date_detail"] = self.safe_p(items, 3)

        # ===== BENEFITS =====
        data["benefits_detail"] = [li.get_text(strip=True) for li in soup.select(".welfare-list li")]

        # ===== DESCRIPTION =====
        data["job_description"] = self.extract_section(soup, "Mô tả Công việc")
        data["job_requirements"] = self.extract_section(soup, "Yêu Cầu Công Việc")

        # ===== OTHER INFO =====
        other = soup.find("h3", string="Thông tin khác")
        if other:
            content = other.find_next("div", class_="content_fck")
            data["other_info"] = content.get_text("\n", strip=True) if content else None

        # ===== TAGS =====
        data["job_tags"] = [a.get_text(strip=True) for a in soup.select(".job-tags a")]

        return data

    # ================= UTIL =================
    def safe_p(self, items, idx):
        if len(items) > idx:
            p = items[idx].select_one("p")
            return p.get_text(strip=True) if p else None
        return None

    def extract_section(self, soup, title: str):
        h = soup.find("h2", string=title)
        if not h:
            return None
        block = h.find_parent("div", class_="detail-row")
        return block.get_text("\n", strip=True) if block else None

    # ================= RUN =================
    def run(self):
        page = 1
        total = 0

        while page <= self.max_page_safe:
            logging.info("PAGE %s", page)

            resp_json = self.fetch_page(page)
            jobs = self.parse_jobs(resp_json)

            if not jobs:
                logging.info("STOP: no jobs")
                break

            # ===== DETAIL CRAWL =====
            for job in jobs:
                try:
                    r = self.session.get(job["job_url"], headers=self.HEADERS, timeout=20)
                    detail = self.parse_job_detail(r.text)
                    job.update(detail)
                except Exception as e:
                    logging.warning("DETAIL FAIL %s: %s", job["job_url"], e)

            save_to_csv(
                jobs=jobs,
                filename=f"careerviet_cntt_page_{page}.csv",
                datasource=self.SOURCE,
            )

            total += len(jobs)
            page += 1

        logging.info("TOTAL JOBS: %s", total)


def main():
    CareerViet(max_page_safe=200).run()


if __name__ == "__main__":
    main()

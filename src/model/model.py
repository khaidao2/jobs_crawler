from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class JobLakeUnified(BaseModel):
    # ========= ID =========
    source: str = Field(..., description="careerviet | vietnamworks | topcv")
    job_id_raw: Optional[str]
    hash_job_id: str

    # ========= CORE =========
    job_title: Optional[str]
    job_url: Optional[str]
    company_name: Optional[str]

    # ========= LOCATION =========
    location_text: Optional[str]
    locations: Optional[List[str]]

    # ========= SALARY =========
    salary_text: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_currency: Optional[str]= "VND"
    salary_visible: Optional[bool]

    # ========= DETAIL =========
    job_description: Optional[str]
    job_requirement: Optional[str]
    benefits: Optional[List[str] | str]
    skills: Optional[List[str]]
    job_level: Optional[str]
    experience: Optional[str]

    # ========= DATE =========
    active_date: Optional[str]
    expire_date: Optional[str]

    # ========= META =========
    crawl_time: datetime
    crawl_page: Optional[int]
    crawl_index: Optional[int]

    # ========= TRACE =========
    raw: Optional[Dict[str, Any]] = Field(
        default=None,
        description="raw payload để trace / replay"
    )

    class Config:
        extra = "ignore"

import pandas as pd
from typing import Dict, List
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from datetime import datetime
import pytz
import os
from google.cloud import storage
import re
import json
from datetime import datetime, timedelta, timezone
from datetime import datetime
import pytz
import hashlib

def get_vn_now() -> datetime:
    """
    Get the current Vietnam datetime (UTC+7).
    """
    vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    return datetime.now(vn_tz)
def create_folder(base_dir: str = "raw_data", datasource: str = "") -> Path:
    """
    Create a folder if it does not exist.
    """
    now=get_vn_now()

    folder_path = Path(base_dir) /datasource
    if datasource:
        folder_path = folder_path / f"{now:%Y%m%d%H}"
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path
def save_to_csv(jobs: List[Dict], filename: str, datasource: str):
    file_path = create_folder(base_dir="raw_data", datasource=datasource) / filename
    df = pd.DataFrame(jobs)
    df.to_csv(file_path, index=False)
    print(f"Saved {len(jobs)} jobs → {file_path}")

def hash_id(source: str, raw_job_id: str, raw_job_url: str) -> str:
    combined = f"{source}|{raw_job_id}|{raw_job_url}".lower().strip()
    return hashlib.md5(combined.encode("utf-8")).hexdigest
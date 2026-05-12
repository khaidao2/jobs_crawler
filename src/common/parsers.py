import re
import os
from typing import Dict, Any

class JobParser:
    """Parse raw job data, transforming text into numeric values and flags."""

    def __init__(self, platform: str):
        self.platform = platform.lower()

    def parse(self, item: Dict[str, Any]) -> Dict[str, Any]:
        if self.platform == "topdev":
            return self._parse_topdev(item)
        elif self.platform == "topcv":
            return self._parse_topcv(item)
        return self._parse_generic(item)

    def _parse_topdev(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return self._parse_generic(item)

    def _parse_topcv(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return self._parse_generic(item)

    def _parse_generic(self, item: Dict[str, Any]) -> Dict[str, Any]:
        salary_raw = item.get('salary', '')
        exp_raw = item.get('experience', '')

        parsed_data = {}
        parsed_data.update(self._parse_salary_string(salary_raw))
        parsed_data.update(self._parse_experience_string(exp_raw))
        return parsed_data

    def _parse_salary_string(self, salary_str: str) -> Dict[str, Any]:
        res = {
            "salary_min": None,
            "salary_max": None,
            "deal_salary": False
        }

        if not salary_str:
            res["deal_salary"] = True
            return res

        if any(word in salary_str.lower() for word in ["thỏa thuận", "negotiable", "deal", "login", "cạnh tranh"]):
            res["deal_salary"] = True
            return res

        s = salary_str.lower().replace(",", ".")
        numbers = re.findall(r"(\d+(?:\.\d+)?)", s)

        if not numbers:
            res["deal_salary"] = True
            return res

        multiplier = 1
        if "triệu" in s:
            multiplier = 1_000_000
        elif "$" in s or "usd" in s:
            multiplier = float(os.environ.get('USD_TO_VND_RATE', '25000'))

        nums = [float(n) * multiplier for n in numbers]

        if len(nums) >= 2:
            res["salary_min"], res["salary_max"] = nums[0], nums[1]
        elif len(nums) == 1:
            if any(w in s for w in ["từ", "trên", "min", ">", "+"]):
                res["salary_min"] = nums[0]
            elif any(w in s for w in ["đến", "tới", "dưới", "max", "<"]):
                res["salary_max"] = nums[0]
            else:
                res["salary_min"] = res["salary_max"] = nums[0]

        return res

    def _parse_experience_string(self, exp_str: str) -> Dict[str, Any]:
        res = {
            "experience_min": None,
            "experience_max": None,
            "experience_not_mentioned": False
        }

        if not exp_str or any(word in exp_str.lower() for word in ["không yêu cầu", "chưa có", "không đề cập", "any"]):
            res["experience_not_mentioned"] = True
            return res

        s = exp_str.lower()
        numbers = re.findall(r"(\d+)", s)

        if not numbers:
            res["experience_not_mentioned"] = True
            return res

        nums = [int(n) for n in numbers]

        if len(nums) >= 2:
            res["experience_min"], res["experience_max"] = nums[0], nums[1]
        elif len(nums) == 1:
            if any(w in s for w in ["trên", "từ", "min", ">", "+"]):
                res["experience_min"] = nums[0]
            elif any(w in s for w in ["dưới", "tới", "đến", "max", "<"]):
                res["experience_max"] = nums[0]
            else:
                res["experience_min"] = res["experience_max"] = nums[0]

        return res

import re
from typing import Dict, Any

class JobParser:
    """
    Parser class to process raw job data from various platforms (TopDev, TopCV, etc.)
    Transforms text strings into numeric values (min/max) and boolean flags.
    """
    
    def __init__(self, platform: str):
        self.platform = platform.lower()

    def parse(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point to parse item data based on the initialized platform.
        """
        if self.platform == "topdev":
            return self._parse_topdev(item)
        elif self.platform == "topcv":
            return self._parse_topcv(item)
        else:
            # Fallback to generic parsing for unknown platforms
            return self._parse_generic(item)

    def _parse_topdev(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Specific logic for TopDev platform."""
        salary_raw = item.get('salary', '')
        exp_raw = item.get('experience', '')
        
        parsed_data = {}
        parsed_data.update(self._parse_salary_string(salary_raw))
        parsed_data.update(self._parse_experience_string(exp_raw))
        
        return parsed_data

    def _parse_topcv(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Specific logic for TopCV platform."""
        salary_raw = item.get('salary', '')
        exp_raw = item.get('experience', '')
        
        parsed_data = {}
        parsed_data.update(self._parse_salary_string(salary_raw))
        parsed_data.update(self._parse_experience_string(exp_raw))
        
        return parsed_data

    def _parse_generic(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Default parsing logic."""
        salary_raw = item.get('salary', '')
        exp_raw = item.get('experience', '')
        
        parsed_data = {}
        parsed_data.update(self._parse_salary_string(salary_raw))
        parsed_data.update(self._parse_experience_string(exp_raw))
        
        return parsed_data

    def _parse_salary_string(self, salary_str: str) -> Dict[str, Any]:
        """Parses salary string into min, max, and deal_salary flag."""
        res = {
            "salary_min": None,
            "salary_max": None,
            "deal_salary": False
        }
        
        # Check for keywords indicating negotiable salary or missing info
        if not salary_str or any(word in salary_str.lower() for word in ["thỏa thuận", "negotiable", "deal", "login", "cạnh tranh"]):
            res["deal_salary"] = True
            return res
        
        # Normalize string: lowercase and replace comma with dot for decimals
        s = salary_str.lower().replace(",", ".")
        # Extract all numbers (integers or decimals)
        numbers = re.findall(r"(\d+(?:\.\d+)?)", s)
        
        if not numbers:
            res["deal_salary"] = True
            return res
        
        # Unit detection and conversion
        multiplier = 1
        if "triệu" in s:
            multiplier = 1_000_000
        elif "usd" in s or "$" in s:
            multiplier = 25_000 # Rough conversion rate to VND
            
        nums = [float(n) * multiplier for n in numbers]
        
        if len(nums) >= 2:
            res["salary_min"], res["salary_max"] = nums[0], nums[1]
        elif len(nums) == 1:
            # Single value detection
            if any(w in s for w in ["từ", "trên", "min", ">", "+"]):
                res["salary_min"] = nums[0]
            elif any(w in s for w in ["đến", "tới", "dưới", "max", "<"]):
                res["salary_max"] = nums[0]
            else:
                # If no direction, assume it's both min and max
                res["salary_min"] = res["salary_max"] = nums[0]
        
        return res

    def _parse_experience_string(self, exp_str: str) -> Dict[str, Any]:
        """Parses experience string into min, max, and experience_not_mentioned flag."""
        res = {
            "experience_min": None,
            "experience_max": None,
            "experience_not_mentioned": False
        }
        
        # Check for keywords indicating no experience required or missing info
        if not exp_str or any(word in exp_str.lower() for word in ["không yêu cầu", "chưa có", "không đề cập", "any"]):
            res["experience_not_mentioned"] = True
            return res
            
        s = exp_str.lower()
        # Extract all integers
        numbers = re.findall(r"(\d+)", s)
        
        if not numbers:
            res["experience_not_mentioned"] = True
            return res
            
        nums = [int(n) for n in numbers]
        
        if len(nums) >= 2:
            res["experience_min"], res["experience_max"] = nums[0], nums[1]
        elif len(nums) == 1:
            # Single value detection with direction
            if any(w in s for w in ["trên", "từ", "min", ">", "+"]):
                res["experience_min"] = nums[0]
            elif any(w in s for w in ["dưới", "tới", "đến", "max", "<"]):
                res["experience_max"] = nums[0]
            else:
                # Fixed year of experience
                res["experience_min"] = res["experience_max"] = nums[0]
                
        return res

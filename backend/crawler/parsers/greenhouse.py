import json
from typing import List, Dict, Any
from backend.crawler.base import BaseParser

class GreenhouseParser(BaseParser):
    """
    Greenhouse ATS API 파서
    URL 예시: https://boards-api.greenhouse.io/v1/boards/{token}/jobs
    """
    
    def __init__(self, site_id: int, board_token: str):
        super().__init__(site_id)
        self.board_token = board_token
            
    @property
    def target_url(self) -> str:
        return f"https://boards-api.greenhouse.io/v1/boards/{self.board_token}/jobs"

    def parse(self, content: str) -> List[Dict[str, Any]]:
        jobs = []
        try:
            content = content.strip() if content else ""
            if not content:
                print(f"[GreenhouseParser] Empty content for {self.board_token}")
                return []
            data = json.loads(content)
            job_list = data.get("jobs", [])
            
            for job in job_list:
                title = job.get("title", "채용공고")
                source_url = job.get("absolute_url", "")
                
                loc = job.get("location", {}).get("name", "")
                depts = job.get("departments", [])
                dept_name = depts[0].get("name", "") if depts else ""
                
                position_parts = []
                if dept_name: position_parts.append(dept_name)
                if loc: position_parts.append(loc)
                position = " / ".join(position_parts) if position_parts else "상세 내용 참고"
                
                # Use board token as company name if not specified
                company = self.board_token.upper()
                deadline = "상시채용"

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": company,
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline
                })
        except Exception as e:
            print(f"[GreenhouseParser] Error parsing json: {e}")
            
        return jobs

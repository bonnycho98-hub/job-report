import json
from typing import List, Dict, Any
from backend.crawler.base import BaseParser

class LeverParser(BaseParser):
    """
    Lever ATS API 파서
    URL 예시: https://api.lever.co/v0/postings/{token}
    """
    
    def __init__(self, site_id: int, board_token: str):
        super().__init__(site_id)
        self.board_token = board_token
            
    @property
    def target_url(self) -> str:
        return f"https://api.lever.co/v0/postings/{self.board_token}"

    def parse(self, content: str) -> List[Dict[str, Any]]:
        jobs = []
        try:
            content = content.strip() if content else ""
            if not content:
                print(f"[LeverParser] Empty content for {self.board_token}")
                return []
            job_list = json.loads(content)
            
            if not isinstance(job_list, list):
                if isinstance(job_list, dict) and not job_list.get("ok", True):
                    print(f"[LeverParser] API error for {self.board_token}: {job_list.get('error')}")
                else:
                    print(f"[LeverParser] Unexpected JSON format for {self.board_token}: {type(job_list)}")
                return []
            
            for job in job_list:
                title = job.get("text", "채용공고")
                source_url = job.get("hostedUrl", "")
                
                categories = job.get("categories", {})
                dept = categories.get("team", "")
                location = categories.get("location", "")
                
                position_parts = []
                if dept: position_parts.append(dept)
                if location: position_parts.append(location)
                position = " / ".join(position_parts) if position_parts else "상세 내용 참고"
                
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
            print(f"[LeverParser] Error parsing json: {e}")
            
        return jobs

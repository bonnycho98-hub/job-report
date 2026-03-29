import json
from typing import List, Dict, Any
from backend.crawler.base import BaseParser

class NineHireParser(BaseParser):
    """
    NineHire(나인하이어) ATS API 파서
    URL 예시: https://api.ninehire.com/identity-access/homepage/recruitments?companyId={companyId}
    """
    
    def __init__(self, site_id: int, company_id: str, public_url: str = ""):
        super().__init__(site_id)
        self.company_id = company_id
        self.public_url = public_url # e.g., https://career.kakaostyle.com
            
    @property
    def target_url(self) -> str:
        return f"https://api.ninehire.com/identity-access/homepage/recruitments?companyId={self.company_id}"

    def parse(self, content: str) -> List[Dict[str, Any]]:
        jobs = []
        try:
            content = content.strip() if content else ""
            if not content:
                print(f"[NineHireParser] Empty content for {self.company_id}")
                return []
                
            data = json.loads(content)
            job_list = data.get("results", [])
            
            for job in job_list:
                title = job.get("title", "채용공고")
                site_url_slug = job.get("siteURL", "")
                
                # NineHire link format
                if self.public_url:
                    source_url = f"{self.public_url.rstrip('/')}/o/{site_url_slug}"
                else:
                    source_url = f"https://ninehire.com/o/{site_url_slug}"
                
                career = job.get("career", {})
                career_type = career.get("type", "")
                emp_types = job.get("employmentType", [])
                
                position_parts = []
                if career_type: position_parts.append(career_type)
                if emp_types: position_parts.extend(emp_types)
                position = " / ".join(position_parts) if position_parts else "상세 내용 참고"
                
                # Deadline
                deadline_type = job.get("deadlineType", "")
                deadline = "상시채용" if deadline_type == "until_filled" else "채용 마감시"

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": "카카오스타일 (지그재그)",
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline
                })
        except Exception as e:
            print(f"[NineHireParser] Error parsing json: {e}")
            
        return jobs

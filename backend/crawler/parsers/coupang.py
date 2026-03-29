from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

class CoupangParser(BaseParser):
    """
    쿠팡(Coupang) 채용공고 파서
    URL: https://www.coupang.jobs/kr/jobs/
    """
    
    def __init__(self, site_id: int):
        super().__init__(site_id)
        self.base_url = "https://www.coupang.jobs"
        
    @property
    def target_url(self) -> str:
        return f"{self.base_url}/kr/jobs/?search=&location=Seoul%2C+South+Korea&origin=global"

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        job_cards = soup.select(".card.card-job")
        
        for card in job_cards:
            try:
                # 1) 제목 및 링크
                link_elem = card.select_one("a.js-view-job")
                if not link_elem:
                    continue
                    
                title = link_elem.text.strip() if link_elem else "쿠팡 채용"
                path = link_elem.get("href", "")
                
                # 상대 경로/절대 경로 처리
                if path.startswith("http"):
                    source_url = path
                elif path.startswith("/"):
                    source_url = f"{self.base_url}{path}"
                else:
                    source_url = f"{self.base_url}/{path}"
                
                # 2) 근무지역(예: 서울)
                position = ""
                meta_item = card.select_one(".job-meta .list-inline-item")
                if meta_item:
                    position = meta_item.text.strip()
                else:
                    position = "직무/부서명 미정"

                deadline = "상시채용" # 보통 쿠팡 경력직은 상시채용
                company = "Coupang"

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": company,
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline
                })
            except Exception as e:
                print(f"[CoupangParser] Error parsing card: {e}")
                
        return jobs

from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

class LineParser(BaseParser):
    """
    라인채용공고 파서
    URL: https://careers.linecorp.com/ko/jobs
    """
    
    def __init__(self, site_id: int):
        super().__init__(site_id)
        self.base_url = "https://careers.linecorp.com"
        
    @property
    def target_url(self) -> str:
        return f"{self.base_url}/ko/jobs"

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        job_cards = soup.select(".job_list li")
        
        for card in job_cards:
            try:
                link_elem = card.select_one("a")
                if not link_elem:
                    continue
                    
                path = link_elem.get("href", "")
                if path.startswith("/"):
                    source_url = f"{self.base_url}{path}"
                else:
                    source_url = f"{self.base_url}/{path}"
                
                title_elem = card.select_one("h3.title")
                title = title_elem.text.strip() if title_elem else "라인 채용"
                
                spans = card.select(".text_filter span")
                company = "LINE"
                position = "포지션 미상"
                
                if len(spans) >= 2:
                    company = spans[1].text.strip()
                if len(spans) >= 3:
                    position = spans[2].text.strip()
                    
                date_elem = card.select_one(".date")
                deadline = date_elem.text.strip() if date_elem else "상시채용"

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": company,
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline
                })
            except Exception as e:
                print(f"[LineParser] Error parsing card: {e}")
                
        return jobs

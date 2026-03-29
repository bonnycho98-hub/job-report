from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

class DunamuParser(BaseParser):
    """
    두나무(Dunamu) 채용공고 파서
    URL: https://careers.dunamu.com
    """
    
    def __init__(self, site_id: int):
        super().__init__(site_id)
        self.base_url = "https://careers.dunamu.com"
        
    @property
    def target_url(self) -> str:
        return self.base_url

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # a.main_list_link
        job_cards = soup.select("a.main_list_link")
        
        for card in job_cards:
            try:
                path = card.get("href", "")
                source_url = f"{self.base_url}{path}" if path.startswith("/") else path
                
                # div:nth-child(2) is title
                divs = card.find_all("div", recursive=False)
                if len(divs) < 2: continue
                
                dept = divs[0].text.strip()
                title_elem = divs[1].select_one("div") or divs[1]
                title = title_elem.text.strip()
                
                # div:nth-child(3) contains spans for career/type
                meta_div = divs[2] if len(divs) > 2 else None
                position_parts = [dept]
                if meta_div:
                    for span in meta_div.find_all("span"):
                        txt = span.text.strip()
                        if txt: position_parts.append(txt)
                
                position = " / ".join(position_parts)
                company = "두나무 (Dunamu)"
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
                print(f"[DunamuParser] Error parsing card: {e}")
                
        return jobs

import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

class NetmarbleParser(BaseParser):
    """
    넷마블(Netmarble) 채용공고 파서
    URL: https://career.netmarble.com/announce
    """
    
    def __init__(self, site_id: int):
        super().__init__(site_id)
        self.base_url = "https://career.netmarble.com"
        
    @property
    def target_url(self) -> str:
        return f"{self.base_url}/announce"

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # li.list_wrap
        job_cards = soup.select("li.list_wrap")
        
        for card in job_cards:
            try:
                title_elem = card.select_one("p.tit")
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                
                # Extract ID from onclick: clickAnnoDetailBtn(1791)
                onclick = title_elem.get("onclick", "")
                match = re.search(r'clickAnnoDetailBtn\((\d+)\)', onclick)
                if match:
                    anno_id = match.group(1)
                    source_url = f"{self.base_url}/announce/view?anno_id={anno_id}"
                else:
                    source_url = self.target_url
                
                # Period
                period_elem = card.select_one("p.period")
                deadline = period_elem.text.strip() if period_elem else "상시채용"
                
                # Hash tags (Category, Studio, Career, etc.)
                hash_tags = card.select("div.hash span")
                position_parts = []
                for tag in hash_tags:
                    txt = tag.text.strip()
                    if txt: position_parts.append(txt)
                
                position = " / ".join(position_parts) if position_parts else "상세 내용 참고"

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": "넷마블 (Netmarble)",
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline
                })
            except Exception as e:
                print(f"[NetmarbleParser] Error parsing card: {e}")
                
        return jobs

from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

class WoowahanParser(BaseParser):
    """
    우아한형제들(배달의민족) 채용공고 파서
    URL: https://career.woowahan.com
    """
    
    def __init__(self, site_id: int):
        super().__init__(site_id)
        self.base_url = "https://career.woowahan.com"
        
    @property
    def target_url(self) -> str:
        return self.base_url

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # The subagent found: div.recruit-list ul.recruit-type-list li
        job_cards = soup.select("div.recruit-list ul.recruit-type-list li")
        
        for card in job_cards:
            try:
                link_elem = card.select_one("a.title")
                if not link_elem:
                    continue
                
                path = link_elem.get("href", "")
                source_url = f"{self.base_url}{path}" if path.startswith("/") else path
                
                title_elem = link_elem.select_one(".title-wrap p")
                if not title_elem:
                    title_elem = link_elem.select_one("span:not(.flag-career)")
                
                title = title_elem.text.strip() if title_elem else "우아한형제들 채용"
                
                career_elem = link_elem.select_one(".flag-career")
                career = career_elem.text.strip() if career_elem else ""
                
                type_elems = card.select(".flag-type span")
                emp_type = type_elems[0].text.strip() if len(type_elems) > 0 else ""
                deadline = type_elems[1].text.strip() if len(type_elems) > 1 else "상시채용"

                position_parts = []
                if career: position_parts.append(career)
                if emp_type: position_parts.append(emp_type)
                position = " / ".join(position_parts) if position_parts else "상세 내용 참고"

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": "우아한형제들 (배달의민족)",
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline
                })
            except Exception as e:
                print(f"[WoowahanParser] Error parsing card: {e}")
                
        return jobs

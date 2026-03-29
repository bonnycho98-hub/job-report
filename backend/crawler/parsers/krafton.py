from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

class KraftonParser(BaseParser):
    """
    크래프톤(KRAFTON) 채용공고 파서
    URL: https://www.krafton.com/careers/jobs/
    """
    
    def __init__(self, site_id: int):
        super().__init__(site_id)
        self.base_url = "https://www.krafton.com"
        
    @property
    def target_url(self) -> str:
        return f"{self.base_url}/careers/jobs/"

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        job_cards = soup.select(".RecruitList-item")
        
        for card in job_cards:
            try:
                # 1) 제목 및 링크
                link_elem = card.select_one("a.RecruitItemTitle-link")
                if not link_elem:
                    continue
                    
                path = link_elem.get("href", "")
                
                if path.startswith("http"):
                    source_url = path
                elif path.startswith("/"):
                    source_url = f"{self.base_url}{path}"
                else:
                    source_url = f"{self.base_url}/{path}"
                
                title_elem = card.select_one(".RecruitItemTitle-title")
                title = title_elem.text.strip() if title_elem else "크래프톤 채용"
                
                # 2) 계열사/스튜디오
                company_elem = card.select_one(".RecruitItemMeta-studio")
                company = company_elem.text.strip() if company_elem else "KRAFTON"
                
                # 3) 직무 및 지역, 고용형태 등
                category_items = card.select(".RecruitItemMetaCategory-item")
                position = ""
                deadline = "상시채용"

                # 예시 구조: [0]: 직무분야, [1]: 고용형태, [2]: 지역
                parts = []
                for item in category_items:
                    parts.append(item.text.strip())
                
                if parts:
                    position = " / ".join(parts) # (ex. Data / Regular / Seoul)

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": company,
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline
                })
            except Exception as e:
                print(f"[KraftonParser] Error parsing card: {e}")
                
        return jobs

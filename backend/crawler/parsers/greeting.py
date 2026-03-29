from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

class GreetingParser(BaseParser):
    """
    Greeting HR (그리팅) 플랫폼 공통 채용공고 파서
    URL 예시: https://11st.career.greetinghr.com, https://wavve.career.greetinghr.com 등
    """
    
    def __init__(self, site_id: int, base_url: str):
        super().__init__(site_id)
        self.base_url = base_url.rstrip("/")
        
    @property
    def target_url(self) -> str:
        # DB의 url 자체를 반환 (각 회사별로 /ko/career 이거나 /o/... 등으로 다를 수 있음)
        return self.base_url

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # 공고 아이템 (a 태그에 data-testid="공고_아이템" 이 있는 경우가 많음)
        # 만약 없다면 li[class*="OpeningItemContainer"] 내부의 a 태그 탐색
        job_cards = soup.select('a[data-testid="공고_아이템"]')
        if not job_cards:
            # Fallback for some greeting sites
            job_cards = soup.select('li[class*="OpeningItemContainer"] a, a[class*="JobCard"]')

        for card in job_cards:
            try:
                path = card.get("href", "")
                if path.startswith("http"):
                    source_url = path
                elif path.startswith("/"):
                    source_url = f"{self.base_url}{path}"
                else:
                    source_url = f"{self.base_url}/{path}"
                
                title_elem = card.select_one('[class*="OpeningListItemTitle-"]')
                title = title_elem.text.strip() if title_elem else "채용공고"
                
                # 메타데이터 (직군, 경력, 고용형태, 근무지)
                position_parts = []
                # Greeting ATS uses subtext spans
                for meta in card.select('span[class*="subtext"], span[data-testid*="공고리스트_subtext_"]'):
                    txt = meta.text.strip()
                    if txt:
                        position_parts.append(txt)
                
                position = " / ".join(position_parts) if position_parts else "상세 내용 참고"
                
                company = self.base_url.split("//")[1].split(".")[0].upper() # ex: 11st, wavve
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
                print(f"[GreetingParser] Error parsing card: {e}")
                
        return jobs

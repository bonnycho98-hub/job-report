import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

class NaverParser(BaseParser):
    """
    네이버(Naver) 채용공고 파서
    URL: https://recruit.navercorp.com/ 또는 https://recruit.navercloudcorp.com/
    """
    
    def __init__(self, site_id: int, base_url: str = "https://recruit.navercorp.com"):
        super().__init__(site_id)
        self.base_url = base_url.rstrip("/")

    @property
    def target_url(self) -> str:
        return f"{self.base_url}/rcrt/list.do"

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # 네이버 채용 목록은 띄워진 HTML의 <li class="card_item"> 형태
        job_cards = soup.select(".card_item")

        for card in job_cards:
            try:
                # 제목
                title_elem = card.select_one(".card_title")
                title = title_elem.text.strip() if title_elem else "네이버 채용"

                # URL 생성을 위한 ID 추출 (onclick="show('30004601')" 속성에 존재)
                link_elem = card.select_one("a.card_link")
                source_url = self.target_url
                if link_elem and link_elem.has_attr("onclick"):
                    match = re.search(r"show\(['\"](\d+)['\"]\)", link_elem["onclick"])
                    if match:
                        job_id = match.group(1)
                        source_url = f"{self.base_url}/rcrt/view.do?annoId={job_id}"

                # 직무 정보, 마감일 정보 등 추출
                # <dl class="card_info"> 하위에 <dd class="info_text"> 들이 순차적으로 위치
                info_texts = card.select("dd.info_text")
                position = "직무/부서명 누락"
                deadline = "상시채용"

                if len(info_texts) >= 5:
                    # 0: 모집부서, 1: 모집분야, 2: 경력, 3: 근로조건, 4: 모집기간
                    dept = info_texts[0].text.strip()
                    field = info_texts[1].text.strip()
                    position = f"{dept} - {field}"
                    deadline = info_texts[4].text.strip()
                elif len(info_texts) > 0:
                    position = info_texts[0].text.strip()

                company = "네이버계열사"
                # 타이틀에서 회사명 뽑아내기 e.g. [NAVER Cloud] ...
                company_match = re.search(r"\[([^\]]+)\]", title)
                if company_match:
                    company = company_match.group(1).strip()
                    
                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": company,
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline
                })
            except Exception as e:
                print(f"[NaverParser] Error parsing card: {e}")
                continue

        return jobs

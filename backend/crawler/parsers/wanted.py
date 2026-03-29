import json
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

class WantedParser(BaseParser):
    """
    원티드(Wanted) 채용공고 파서
    원티드는 Next.js 기반으로 초기 데이터가 <script id="__NEXT_DATA__"> 에 포함되어 있는 경우가 많습니다.
    또는 API 호출 응답을 가로채거나 페이지 내 렌더링된 특정 DOM 요소를 파싱할 수 있습니다.
    여기서는 BeautifulSoup을 사용해 렌더링된 DOM 내용 기반으로 크롤링하는 예시입니다.
    """

    @property
    def target_url(self) -> str:
        # 이 URL은 크롤러 엔진에서 site.url 로 덮어씌워지거나 오버라이드될 수 있음
        return "https://www.wanted.co.kr/wdlist?country=kr&job_sort=job.latest_order&years=-1&locations=all"

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # 원티드의 공고 리스트 아이템 선택자 (클래스명은 사이트 개편 시 변경될 수 있음)
        # 예: data-cy="job-card" 속성을 가진 요소들
        job_cards = soup.select('div[data-cy="job-card"]')

        for card in job_cards:
            try:
                # 1. URL 추출 파싱
                a_tag = card.find('a')
                if not a_tag or not a_tag.get('href'):
                    continue
                href = a_tag['href']
                source_url = f"https://www.wanted.co.kr{href}" if href.startswith('/') else href

                # 2. 직무(포지션) 및 회사명 파싱
                # 보통 원티드는 직무명이 strong 또는 class명으로 강조됨
                position_elem = card.select_one('.job-card-position') # 예시 클래스명
                company_elem = card.select_one('.job-card-company-name') # 예시 클래스명

                position = position_elem.text.strip() if position_elem else "직무 미상"
                company = company_elem.text.strip() if company_elem else "회사명 미상"

                # 3. 보상, 지역 등 기타 정보
                # 원티드는 특별한 마감일 표기보단 상시 채용이 많으므로 기본값 처리
                deadline = "상시채용"

                title = f"[{company}] {position}"

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": company,
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline
                })
            except Exception as e:
                # 일부 카드 파싱 에러는 무시하고 다음 카드 진행
                print(f"[WantedParser] Error parsing card: {e}")
                continue

        return jobs

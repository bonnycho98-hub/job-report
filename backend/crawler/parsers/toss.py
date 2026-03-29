import json
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

class TossParser(BaseParser):
    """
    토스(Toss) 채용공고 파서
    URL: https://toss.im/career/jobs
    """

    @property
    def target_url(self) -> str:
        return "https://toss.im/career/jobs"

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # 토스의 경우 Next.js 데이터 속성을 사용하거나 렌더링된 특정 a 태그 리스트일 수 있습니다.
        # MVP 모델이므로 일단 a 태그 중 href가 /career/job-detail 형태인 항목을 공고로 간주.
        # (실무에서는 API 응답을 가로채거나 좀 더 명확한 CSS Selector를 분석해 적용해야 합니다)
        job_links = soup.find_all('a', href=lambda h: h and '/career/job-detail' in h)
        
        # 중복 방지를 위한 셋(Set) 사용 (동일 공고가 모바일/PC 레이아웃에 중복 등장 시)
        seen_urls = set()

        for a_tag in job_links:
            try:
                href = a_tag['href']
                source_url = f"https://toss.im{href}" if href.startswith('/') else href
                
                if source_url in seen_urls:
                    continue
                seen_urls.add(source_url)

                # 보통 채용 공고 리스트 아이템 내부의 텍스트가 직무 제목이 됨
                # 토스는 보통 1번째 span 또는 div에 타이틀 포지션명 존재.
                # 단순화하여 태그 내 전체 텍스트를 파싱.
                position = a_tag.get_text(separator=" ", strip=True) 
                
                # 원티드처럼 내부 DOM이 복잡할 수 있으나, 일단 가장 긴 텍스트 내용을 직무로 유추
                if len(position) < 3:
                     continue # 텍스트가 너무 짧으면 무시

                company = "토스(Toss)"
                title = f"[{company}] {position[:30]}..." if len(position) > 30 else f"[{company}] {position}"
                deadline = "상시채용" # 토스 대부분 상시

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": company,
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline
                })
            except Exception as e:
                print(f"[TossParser] Error parsing item: {e}")
                continue

        return jobs

import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

class CjParser(BaseParser):
    """
    CJ 그룹 채용공고 파서
    URL: https://recruit.cj.net/recruit/ko/recruit/recruit/list.fo
    """

    @property
    def target_url(self) -> str:
        return "https://recruit.cj.net/recruit/ko/recruit/recruit/list.fo"

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # 공고 리스트 아이템 찾기
        job_links = soup.find_all('a')

        for a_tag in job_links:
            try:
                href = a_tag.get('href', '')
                if 'detail.fo' not in href and 'bestDetail.fo' not in href:
                    continue
                
                # Full URL 만들기
                source_url = href
                if source_url and source_url.startswith('/'):
                    source_url = f"https://recruit.cj.net{source_url}"
                elif not source_url.startswith('http'):
                    # href가 자바스크립트가 아니거나 상대경로일 경우 처리 (기본 제공 href가 절대경로 형태인지 확인)
                    source_url = href

                # 태그 내의 텍스트 노드들 추출
                texts = list(a_tag.stripped_strings)
                if not texts:
                    continue
                
                # CJ의 경우 보통 구조가: 
                # [상태/D-데이, 계열사, 신입/경력, 공고제목, 기한] 등.
                # 예: ['D-13', 'CJ프레시웨이', '경력', '[CJ프레시웨이] 식품 PM 경력사원 모집', 'New', '2026.02.20 ~ 2026.03.06']
                # 또는 ['D-11', 'CJ푸드빌', '경력', '[CJ푸드빌] 재무팀 회계/연결결산 (5년 이상)', '2026.02.19 ~ 2026.03.04']
                
                # 회사명 찾기 (주로 'CJ'로 시작하는 키워드, 혹은 1~2번째 인덱스)
                company = "CJ계열사"
                for t in texts:
                    if t.startswith('CJ'):
                        company = t
                        break
                
                # 마감일 (마지막 요소 부근, 보통 날짜 형식이거나 '채용시까지' 포함)
                deadline = texts[-1]
                
                # 공고 제목 찾기 (제일 긴 문자열을 제목으로 간주하거나, 회사명 뒤에 나오는 긴 문자열)
                # 'D-', '상시', 계열사명, '신입', '경력', 'New', 날짜 형식을 제외한 것 중 가장 긴 것
                exclude_keywords = ['D-', '상시', '신입', '경력', 'New', '채용시까지']
                possible_titles = []
                for t in texts:
                    if t == company: continue
                    if any(exclude.lower() in t.lower() for exclude in exclude_keywords) and '[' not in t:
                        continue
                    # "2026." 등으로 시작하는 날짜 패턴 제외
                    if re.match(r"^\d{4}\.", t):
                        continue
                    possible_titles.append(t)
                
                title = max(possible_titles, key=len) if possible_titles else "제목 없음"
                
                position = title  # CJ 공고는 제목에 포지션이 포함된 경우가 많음

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": company,
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline
                })
            except Exception as e:
                print(f"[CjParser] Error parsing card: {e}")
                continue

        # 중복 제거 (같은 URL 공고가 여러 개 발견될 수 있음)
        unique_jobs = {job['source_url']: job for job in jobs}.values()
        
        return list(unique_jobs)

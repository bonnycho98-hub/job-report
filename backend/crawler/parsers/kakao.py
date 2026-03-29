from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

class KakaoParser(BaseParser):
    """
    카카오(Kakao) 채용공고 파서
    URL: https://careers.kakao.com/jobs
    """

    @property
    def target_url(self) -> str:
        # 사용자가 제공한 TECHNOLOGY 파트, KAKAO 컴퍼니 필터링된 URL
        return "https://careers.kakao.com/jobs?skillSet=&page=1&company=KAKAO&part=TECHNOLOGY&employeeType=&keyword="

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # 카카오 채용 목록은 <ul class="list_jobs"> 하위의 <a> 태그들
        # 브라우저 subagent 분석에 따르면 <a>가 <li>를 감싸고 있음
        items = soup.select("ul.list_jobs > a")

        for item in items:
            try:
                # 제목
                title_elem = item.select_one("h4.tit_jobs")
                title = title_elem.get_text(strip=True) if title_elem else "카카오 채용"

                # URL
                href = item.get("href")
                source_url = f"https://careers.kakao.com{href}" if href else self.target_url

                # 회사명 (dl.item_subinfo:nth-of-type(1) dd)
                subinfos = item.select("dl.item_subinfo")
                company = "카카오"
                if len(subinfos) > 0:
                    company_dd = subinfos[0].select_one("dd")
                    company = company_dd.get_text(strip=True) if company_dd else "카카오"

                # 포지션/태그
                tags = item.select("div.list_tag span.link_tag")
                position = ", ".join([tag.get_text(strip=True) for tag in tags]) if tags else "TECHNOLOGY"

                # 마감일 (dl.list_info dd)
                deadline_elem = item.select_one("dl.list_info dd")
                deadline = deadline_elem.get_text(strip=True) if deadline_elem else "상시채용"

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": company,
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline
                })
            except Exception as e:
                print(f"[KakaoParser] Error parsing item: {e}")
                continue

        return jobs

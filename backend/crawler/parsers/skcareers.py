from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser


class SkCareersParser(BaseParser):
    """
    SK Careers (skcareers.com) 채용공고 파서
    URL 예시: https://www.skcareers.com/Recruit/Index?searchText=티맵모빌리티
    """

    def __init__(self, site_id: int, base_url: str):
        super().__init__(site_id)
        self.base_url = base_url

    @property
    def target_url(self) -> str:
        return self.base_url

    @property
    def wait_selector(self) -> str | None:
        return "#RecruitList .list-item"

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, "html.parser")
        jobs = []

        for item in soup.select("#RecruitList .list-item"):
            try:
                a = item.select_one("a.list-link")
                if not a:
                    continue

                source_url = a.get("href", "")
                title_elem = item.select_one("h2.title")
                title = title_elem.text.strip() if title_elem else "채용공고"

                company_elem = item.select_one(".company")
                company = company_elem.text.strip() if company_elem else "SK"

                job_role_elem = item.select_one(".detail.jobRole")
                recruit_type_elem = item.select_one(".item.recruitType")
                working_area_elem = item.select_one(".item.workingArea")
                parts = [e.text.strip() for e in [job_role_elem, recruit_type_elem, working_area_elem] if e]
                position = " / ".join(parts) if parts else "상세 내용 참고"

                date_elem = item.select_one(".date")
                deadline = date_elem.text.strip() if date_elem else "상시채용"

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": company,
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline,
                })
            except Exception as e:
                print(f"[SkCareersParser] Error parsing item: {e}")

        return jobs

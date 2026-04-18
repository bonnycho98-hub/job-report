from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

class BankSaladParser(BaseParser):
    """
    뱅크샐러드 채용공고 파서
    URL: https://corp.banksalad.com/jobs/
    JS 렌더링 페이지 → Playwright로 렌더링 후 파싱
    """

    def __init__(self, site_id: int):
        super().__init__(site_id)

    @property
    def target_url(self) -> str:
        return "https://corp.banksalad.com/jobs/"

    @property
    def wait_selector(self) -> str:
        return "[class*='JobItem']"

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []

        # 부서(department) 단위로 순회하여 position 정보를 함께 수집
        departments = soup.select('[class*="JobDepartment"]')
        for dept in departments:
            dept_name = dept.get("id", "")
            if not dept_name:
                title_el = dept.select_one('[class*="DepartmentTitle"]')
                dept_name = title_el.text.strip() if title_el else ""

            for item in dept.select('a[class*="JobLink"]'):
                href = item.get("href", "")
                if not href:
                    continue

                # 아이콘 img 제거 후 텍스트만 추출
                for img in item.find_all("img"):
                    img.decompose()
                title = item.get_text(strip=True)
                if not title:
                    continue

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": "뱅크샐러드",
                    "position": dept_name,
                    "source_url": href,
                    "deadline": "상시채용",
                })

        return jobs

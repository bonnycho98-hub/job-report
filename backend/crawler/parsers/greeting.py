import json
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser

CAREER_TYPE_MAP = {
    "EXPERIENCED": "경력",
    "NEW": "신입",
    "REGARDLESS": "경력무관",
}

EMPLOYMENT_TYPE_MAP = {
    "FULL_TIME_WORKER": "정규직",
    "CONTRACT_WORKER": "계약직",
    "INTERN": "인턴",
    "PART_TIME_WORKER": "파트타임",
}


class GreetingParser(BaseParser):
    """
    Greeting HR (그리팅) 플랫폼 공통 채용공고 파서
    URL 예시: https://11st.career.greetinghr.com/ko/apply, https://gccompany.career.greetinghr.com/ko/apply 등
    __NEXT_DATA__ JSON에서 채용공고를 파싱하고, 없을 경우 HTML fallback 사용.
    """

    def __init__(self, site_id: int, base_url: str):
        super().__init__(site_id)
        self.base_url = base_url.rstrip("/")
        # 도메인 origin만 추출 (e.g. https://gccompany.career.greetinghr.com)
        m = re.match(r"(https?://[^/]+)", self.base_url)
        self.origin = m.group(1) if m else self.base_url

    @property
    def target_url(self) -> str:
        return self.base_url

    @property
    def wait_selector(self) -> str | None:
        return 'a[href*="/ko/o/"], a[data-testid="공고_아이템"]'

    def _parse_from_next_data(self, html_content: str) -> List[Dict[str, Any]] | None:
        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            html_content,
            re.DOTALL,
        )
        if not m:
            return None
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            return None

        queries = (
            data.get("props", {})
            .get("pageProps", {})
            .get("dehydratedState", {})
            .get("queries", [])
        )
        openings_query = next(
            (q for q in queries if q.get("queryKey") == ["openings"]), None
        )
        if openings_query is None:
            return None

        openings = openings_query.get("state", {}).get("data", [])
        if not isinstance(openings, list):
            return None

        # company name from any group entry
        company_name = ""
        for o in openings:
            if o.get("group", {}).get("name"):
                company_name = o["group"]["name"]
                break

        jobs = []
        for opening in openings:
            try:
                opening_id = opening.get("openingId")
                title = opening.get("title", "채용공고")
                source_url = f"{self.origin}/ko/o/{opening_id}"

                due_date = opening.get("dueDate")
                deadline = due_date[:10] if due_date else "상시채용"

                position_parts = []
                jp = opening.get("openingJobPosition")
                if jp:
                    positions = jp.get("openingJobPositions", [])
                    if positions:
                        pos = positions[0]
                        occ = pos.get("workspaceOccupation")
                        if occ:
                            position_parts.append(occ.get("occupation", ""))
                        career = pos.get("jobPositionCareer")
                        if career:
                            ct = CAREER_TYPE_MAP.get(career.get("careerType", ""), "")
                            if ct:
                                position_parts.append(ct)
                        emp = pos.get("jobPositionEmployment")
                        if emp:
                            et = EMPLOYMENT_TYPE_MAP.get(career.get("employmentType", "") if career else emp.get("employmentType", ""), "")
                            et = EMPLOYMENT_TYPE_MAP.get(emp.get("employmentType", ""), "")
                            if et:
                                position_parts.append(et)
                        place = pos.get("workspacePlace")
                        if place and place.get("location"):
                            position_parts.append(place["location"])

                position = " / ".join(p for p in position_parts if p) or "상세 내용 참고"

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": company_name or self.origin.split("//")[1].split(".")[0],
                    "position": position,
                    "source_url": source_url,
                    "deadline": deadline,
                })
            except Exception as e:
                print(f"[GreetingParser] Error parsing opening {opening.get('openingId')}: {e}")

        return jobs

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        result = self._parse_from_next_data(html_content)
        if result is not None:
            return result

        # HTML fallback
        soup = BeautifulSoup(html_content, "html.parser")
        jobs = []
        job_cards = soup.select('a[data-testid="공고_아이템"]')
        if not job_cards:
            job_cards = soup.select('li[class*="OpeningItemContainer"] a, a[class*="JobCard"]')

        for card in job_cards:
            try:
                path = card.get("href", "")
                if path.startswith("http"):
                    source_url = path
                elif path.startswith("/"):
                    source_url = f"{self.origin}{path}"
                else:
                    source_url = f"{self.origin}/{path}"

                title_elem = card.select_one('[class*="OpeningListItemTitle-"]')
                title = title_elem.text.strip() if title_elem else "채용공고"

                position_parts = []
                for meta in card.select('span[class*="subtext"], span[data-testid*="공고리스트_subtext_"]'):
                    txt = meta.text.strip()
                    if txt:
                        position_parts.append(txt)

                position = " / ".join(position_parts) if position_parts else "상세 내용 참고"
                company = self.origin.split("//")[1].split(".")[0].upper()

                jobs.append({
                    "site_id": self.site_id,
                    "title": title,
                    "company": company,
                    "position": position,
                    "source_url": source_url,
                    "deadline": "상시채용",
                })
            except Exception as e:
                print(f"[GreetingParser] Error parsing card: {e}")

        return jobs

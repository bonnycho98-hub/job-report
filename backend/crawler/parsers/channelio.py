import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.crawler.base import BaseParser


class ChannelIOParser(BaseParser):
    """
    채널톡(Channel.io) 채용공고 파서
    URL: https://channel.io/ko/careers
    SSR Next.js / styled-components 페이지

    DOM 구조 (클래스명은 빌드마다 해시가 달라질 수 있어 구조 기반으로 파싱):
      a[href="/ko/careers/UUID"]       ← 공고 링크 (레벨 0)
        └ parent: job card wrapper     (레벨 1)
          └ parent: JobList div        (레벨 2)
            └ parent: dept section div (레벨 3)  ← 첫 번째 div 자식이 부서명
              ├ div (Header)  → 부서명 텍스트 (짧음, <40자)
              └ div (JobList) → 공고 목록
    """

    UUID_RE = re.compile(r"^/(?:ko|en)/careers/[0-9a-f\-]{36}$")

    @property
    def target_url(self) -> str:
        return "https://channel.io/ko/careers"

    @property
    def wait_selector(self) -> str:
        return "a[href*='/careers/']"

    def _get_dept_from_ancestor(self, a_tag) -> str:
        """<a> 태그 기준 부모 체인에서 부서명을 추출한다."""
        el = a_tag
        for _ in range(6):
            el = el.parent
            if el is None:
                break
            # 직계 자식 중 짧은 텍스트만 있는 div → 부서명 헤더
            for child in el.children:
                if not hasattr(child, 'get_text'):
                    continue
                text = child.get_text(strip=True)
                # 부서명은 40자 이하의 짧은 텍스트
                if text and len(text) <= 40 and child.name == 'div':
                    # 자식이 없거나 하나뿐인 단순 div (중첩 공고 목록 div 제외)
                    sub_links = child.find_all("a", href=self.UUID_RE)
                    if not sub_links:
                        return text
        return ""

    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, "html.parser")
        jobs = []
        seen: set = set()

        for a_tag in soup.find_all("a", href=self.UUID_RE):
            href = a_tag.get("href", "")
            source_url = f"https://channel.io{href}"

            if source_url in seen:
                continue
            seen.add(source_url)

            # 제목: JobTitle 클래스 p 우선, 없으면 첫 번째 p
            title_elem = a_tag.find("p", class_=lambda c: c and any("JobTitle" in cls for cls in c))
            if not title_elem:
                title_elem = a_tag.find("p")
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            if not title:
                continue

            dept = self._get_dept_from_ancestor(a_tag)

            jobs.append({
                "site_id": self.site_id,
                "title": title,
                "company": "채널톡",
                "position": dept,
                "source_url": source_url,
                "deadline": "상시채용",
            })

        return jobs

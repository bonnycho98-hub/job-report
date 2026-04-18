import json
from typing import List, Dict, Any
from backend.crawler.base import BaseParser

class TossParser(BaseParser):
    """
    토스(Toss) 채용공고 파서
    toss.im이 내부적으로 호출하는 공개 API를 직접 사용.
    Playwright 불필요 — 클라우드 서버 IP 차단 우회.
    """

    @property
    def target_url(self) -> str:
        return "https://api-public.toss.im/api/v3/ipd-eggnog/career/job-groups"

    def parse(self, content: str) -> List[Dict[str, Any]]:
        jobs = []
        try:
            data = json.loads(content)
            job_list = data.get("success", [])

            for item in job_list:
                try:
                    title = item.get("title", "").strip()
                    if not title:
                        continue

                    primary_job = item.get("primary_job", {})
                    source_url = primary_job.get("absolute_url", "")

                    # 메타데이터에서 자회사명과 키워드 추출
                    meta = {m["name"]: m.get("value", "") for m in primary_job.get("metadata", [])}
                    company = meta.get("포지션의 소속 자회사를 선택해 주세요.", "토스")
                    keywords_raw = meta.get(
                        "외부 노출용 키워드를 입력해주세요. (최대 4개  / 1번 키워드 = 포지션 카테고리 / 나머지 키워드 = 포지션 특성에 맞게 작성)",
                        ""
                    )
                    position = keywords_raw.replace(",", " · ") if keywords_raw else title

                    jobs.append({
                        "site_id": self.site_id,
                        "title": title,
                        "company": company,
                        "position": position,
                        "source_url": source_url,
                        "deadline": "상시채용",
                    })
                except Exception as e:
                    print(f"[TossParser] item 파싱 오류: {e}")
                    continue

        except Exception as e:
            print(f"[TossParser] JSON 파싱 오류: {e}")

        return jobs

import json
from typing import List, Dict, Any
from backend.crawler.base import BaseParser

class WoowahanParser(BaseParser):
    """
    우아한형제들(배달의민족) 채용공고 파서
    공개 API를 직접 사용해 전체 공고를 한 번에 수집.
    """

    @property
    def target_url(self) -> str:
        return "https://career.woowahan.com/w1/recruits?category=all%3Aall&recruitCampaignSeq=0&all=all&page=0&size=200&sort=updateDate%2Cdesc"

    def parse(self, content: str) -> List[Dict[str, Any]]:
        jobs = []
        try:
            data = json.loads(content)
            items = data.get("data", {}).get("list", [])

            for item in items:
                try:
                    title = item.get("recruitName", "").strip()
                    if not title:
                        continue

                    recruit_number = item.get("recruitNumber", "")
                    source_url = f"https://career.woowahan.com/recruitment/{recruit_number}/detail" if recruit_number else "https://career.woowahan.com/recruitment/"

                    end_date = item.get("recruitEndDate", "")
                    deadline = "상시채용" if not end_date or end_date.startswith("9999") or end_date.startswith("2999") else end_date[:10]

                    career_code = (item.get("careerType") or {}).get("recruitItemCode", "")
                    career_map = {
                        "BA003001": "신입", "BA003002": "경력",
                        "BA003003": "경력무관", "BA003004": "신입/경력",
                    }
                    career = career_map.get(career_code, "")

                    emp_code = (item.get("employmentType") or {}).get("recruitItemCode", "")
                    emp_map = {
                        "BA002001": "정규직", "BA002002": "계약직",
                        "BA002003": "인턴", "BA002004": "파견직",
                    }
                    emp_type = emp_map.get(emp_code, "")

                    position_parts = [p for p in [career, emp_type] if p]
                    position = " / ".join(position_parts) if position_parts else "상세 내용 참고"

                    jobs.append({
                        "site_id": self.site_id,
                        "title": title,
                        "company": "우아한형제들 (배달의민족)",
                        "position": position,
                        "source_url": source_url,
                        "deadline": deadline,
                    })
                except Exception as e:
                    print(f"[WoowahanParser] item 파싱 오류: {e}")
                    continue

        except Exception as e:
            print(f"[WoowahanParser] JSON 파싱 오류: {e}")

        return jobs

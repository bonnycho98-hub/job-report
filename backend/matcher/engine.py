import re
from typing import List, Dict, Any

# 정의된 키워드 (소문자 변환하여 비교 용이하게 함)
PROFILES = {
    "웅키": {
        "name": "웅키",
        "sub_groups": {
            "A-1": ["마케팅", "marketing", "프로모션", "promotion", "onsite"]
        }
    },
    "쵸키": {
        "name": "쵸키",
        "sub_groups": {
            "B-1": [
                "서비스운영", "서비스 운영", "service operations", "operations manager",
                "운영기획", "운영 기획", "운영관리", "정책 운영", "정책 설계",
                "프로세스 개선", "프로세스 설계", "bizops", "business operations",
                "업무 효율화", "운영 자동화", "voc", "product operations"
            ],
            "B-2": [
                "pm", "product manager", "프로덕트 매니저", "growth pm",
                "growth operation", "program"
            ],
            "B-3": [
                "기획자", "서비스기획", "서비스 기획"
            ],
            "B-4": [
                "cs", "cx", "customer success", "customer experience",
                "고객경험", "고객 경험", "고객성공", "고객 성공", "고객지원", "고객 지원"
            ]
        }
    }
}

class MatcherEngine:
    def __init__(self):
        # 미리 정규식 컴파일 등 수행 가능 (여기는 단순 포함 확인으로 시작)
        pass

    def evaluate(self, text: str) -> List[Dict[str, Any]]:
        """
        주어진 텍스트(제목+포지션 등)를 바탕으로 각 프로필/서브그룹별 매칭 점수와 키워드 반환.
        매칭된 항목만 리스트로 반환.
        """
        results = []
        text_lower = text.lower()

        for profile_id, profile_data in PROFILES.items():
            profile_name = profile_data["name"]
            
            for sub_group, keywords in profile_data["sub_groups"].items():
                matched_keywords = []
                # 아주 단순한 문자열 포함 매칭 (추후 정규식 단어 경계 \b 활용 가능)
                for kw in keywords:
                    if kw in text_lower:
                        matched_keywords.append(kw)
                
                if matched_keywords:
                    # 키워드 1개당 10점씩 단순 환산 (혹은 개수 자체를 점수로 사용)
                    score = len(matched_keywords) * 10.0
                    results.append({
                        "profile_id": profile_id,
                        "profile_name": profile_name,
                        "sub_group": sub_group,
                        "match_score": score,
                        "matched_keywords": matched_keywords
                    })
        
        return results

matcher_engine = MatcherEngine()

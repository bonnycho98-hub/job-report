from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseParser(ABC):
    """
    모든 채용 사이트 파서가 상속받아야 하는 기본 인터페이스.
    """
    
    def __init__(self, site_id: int):
        self.site_id = site_id

    @property
    @abstractmethod
    def target_url(self) -> str:
        """크롤링 타겟 메인 URL (예: 채용공고 리스트 페이지)"""
        pass

    @property
    def wait_selector(self) -> str | None:
        """페이지 로드 후 추가로 대기할 CSS 셀렉터 (None이면 생략)"""
        return None

    @abstractmethod
    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        """
        HTML 콘텐츠를 받아 채용공고 데이터(dict)의 리스트를 추출하여 반환.
        반환 예시:
        [{
            "title": "...", "company": "...", "position": "...",
            "source_url": "...", "deadline": "..."
        }]
        """
        pass

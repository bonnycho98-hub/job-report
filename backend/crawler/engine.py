import logging
import asyncio
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend import crud, schemas
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class CrawlerEngine:
    def __init__(self, db: Session):
        self.db = db
        self.parsers = {} # {site_id: BaseParser 인스턴스} 등록 공간

    def register_parser(self, site_id: int, parser_instance):
        self.parsers[site_id] = parser_instance

    async def run(self) -> Dict[str, Any]:
        """
        등록된 사이트를 비동기로 크롤링하고 수집된 데이터를 반환.
        """
        active_sites = [s for s in crud.get_sites(self.db) if s.status != "disabled"]
        results = {
            "total_sites": len(active_sites),
            "success": 0,
            "failed": 0,
            "errors": [],
            "raw_jobs": []
        }

        if not active_sites:
            return results

        async with async_playwright() as p:
            # 브라우저 띄우지 않고 실행 (headless=True)
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            )
            page = await browser.new_page(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            for site in active_sites:
                if site.id not in self.parsers:
                    # MVP 테스트를 위한 모의(Mock) 파서 및 실제 파서 분기
                    if "wanted.co.kr" in site.url:
                        from backend.crawler.parsers.wanted import WantedParser
                        parser = WantedParser(site.id)
                    elif "toss.im" in site.url:
                        from backend.crawler.parsers.toss import TossParser
                        parser = TossParser(site.id)
                    elif "navercorp.com" in site.url:
                        from backend.crawler.parsers.naver import NaverParser
                        parser = NaverParser(site.id)
                    elif any(domain in site.url for domain in ["navercloudcorp.com", "naverfincorp.com", "webtoonscorp.com", "snowcorp.com", "naverlabs.com"]):
                        from backend.crawler.parsers.naver import NaverParser
                        parser = NaverParser(site.id, base_url=site.url)
                    elif "cj.net" in site.url:
                        from backend.crawler.parsers.cj import CjParser
                        parser = CjParser(site.id)
                    elif "kakao.com" in site.url:
                        from backend.crawler.parsers.kakao import KakaoParser
                        parser = KakaoParser(site.id)
                    elif "greetinghr.com" in site.url:
                        from backend.crawler.parsers.greeting import GreetingParser
                        parser = GreetingParser(site.id, base_url=site.url)
                    elif "greenhouse.io" in site.url:
                        from backend.crawler.parsers.greenhouse import GreenhouseParser
                        # 추출 예시: https://boards-api.greenhouse.io/v1/boards/{token}/jobs
                        token = site.url.split("/")[-2]
                        parser = GreenhouseParser(site.id, board_token=token)
                    elif "api.lever.co" in site.url:
                        from backend.crawler.parsers.lever import LeverParser
                        # 추출 예시: https://api.lever.co/v0/postings/{token}
                        token = site.url.split("/")[-1]
                        parser = LeverParser(site.id, board_token=token)
                    elif "api.ninehire.com" in site.url:
                        from backend.crawler.parsers.ninehire import NineHireParser
                        import urllib.parse
                        parsed = urllib.parse.urlparse(site.url)
                        company_id = urllib.parse.parse_qs(parsed.query).get("companyId", [""])[0]
                        # For Kakao Style, we know the public URL
                        public_url = "https://career.kakaostyle.com" if "kakaostyle" in site.name.lower() else ""
                        parser = NineHireParser(site.id, company_id=company_id, public_url=public_url)
                    elif "woowahan.com" in site.url:
                        from backend.crawler.parsers.woowahan import WoowahanParser
                        parser = WoowahanParser(site.id)
                    elif "dunamu.com" in site.url:
                        from backend.crawler.parsers.dunamu import DunamuParser
                        parser = DunamuParser(site.id)
                    elif "netmarble.com" in site.url:
                        from backend.crawler.parsers.netmarble import NetmarbleParser
                        parser = NetmarbleParser(site.id)
                    elif "linecorp.com" in site.url:
                        from backend.crawler.parsers.line import LineParser
                        parser = LineParser(site.id)
                    elif "coupang.jobs" in site.url:
                        from backend.crawler.parsers.coupang import CoupangParser
                        parser = CoupangParser(site.id)
                    elif "corp.banksalad.com" in site.url:
                        from backend.crawler.parsers.banksalad import BankSaladParser
                        parser = BankSaladParser(site.id)
                    elif "krafton.com" in site.url:
                        from backend.crawler.parsers.krafton import KraftonParser
                        parser = KraftonParser(site.id)
                    elif "skcareers.com" in site.url:
                        from backend.crawler.parsers.skcareers import SkCareersParser
                        parser = SkCareersParser(site.id, base_url=site.url)
                    elif "channel.io" in site.url:
                        from backend.crawler.parsers.channelio import ChannelIOParser
                        parser = ChannelIOParser(site.id)
                    else:
                        from backend.crawler.base import BaseParser
                        class MockParser(BaseParser):
                            @property
                            def target_url(self) -> str: return site.url
                            def parse(self, html_content: str):
                                return [
                                    {"site_id": self.site_id, "title": "[테스트] 글로벌 마케팅 매니저", "company": site.name, "position": "마케팅", "source_url": f"{site.url}/1", "deadline": "2026-03-31"},
                                    {"site_id": self.site_id, "title": "[테스트] 그로스 프로덕트 매니저(PM)", "company": site.name, "position": "서비스운영, 웹 기획", "source_url": f"{site.url}/2", "deadline": "상시채용"}
                                ]
                        parser = MockParser(site.id)
                else:
                    parser = self.parsers[site.id]
                try:
                    response = await page.goto(parser.target_url, wait_until="networkidle", timeout=30000)

                    # wait_selector가 있으면 해당 요소가 DOM에 나타날 때까지 추가 대기
                    if parser.wait_selector:
                        try:
                            await page.wait_for_selector(parser.wait_selector, timeout=30000)
                        except Exception:
                            logger.warning(f"wait_selector '{parser.wait_selector}' not found for {site.name}")

                    # API 파서인 경우 JSON 전용 처리가 필요할 수 있음
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        content = await response.text()
                    else:
                        # 브라우저가 JSON을 <pre> 태그 등으로 감싸는 경우 대비
                        if any(x in parser.target_url for x in ["greenhouse.io", "api.lever.co", "api.ninehire.com", "api-public.toss.im", "career.woowahan.com/w1"]):
                            content = await page.evaluate("() => document.body.innerText")
                        else:
                            content = await page.content()
                    
                    # 1페이지 파싱
                    parsed_jobs = parser.parse(content)
                    results["raw_jobs"].extend(parsed_jobs)

                    # 추가 페이지 순회 (page_count > 1인 파서)
                    total_pages = parser.page_count(content)
                    for page_num in range(2, total_pages + 1):
                        try:
                            await page.goto(parser.get_page_url(page_num), wait_until="networkidle", timeout=30000)
                            if parser.wait_selector:
                                await page.wait_for_selector(parser.wait_selector, timeout=15000)
                            extra_content = await page.content()
                            results["raw_jobs"].extend(parser.parse(extra_content))
                        except Exception as pe:
                            logger.warning(f"[{site.name}] page {page_num} 실패: {pe}")
                            break

                    results["success"] += 1

                    # 성공 상태 업데이트
                    crud.update_site_status(self.db, site.id, "active")

                except Exception as e:
                    logger.error(f"Error crawling site {site.name}: {e}")
                    results["failed"] += 1
                    results["errors"].append({"site_id": site.id, "site_name": site.name, "error": str(e)})
                    
                    # DB 상태를 error로 업데이트
                    crud.update_site_status(self.db, site.id, "parse_error")
                    
            await browser.close()

        return results

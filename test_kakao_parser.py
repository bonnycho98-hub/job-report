import asyncio
from backend.crawler.parsers.kakao import KakaoParser
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        url = "https://careers.kakao.com/jobs?skillSet=&page=1&company=KAKAO&part=TECHNOLOGY&employeeType=&keyword="
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until='networkidle')
        html = await page.content()
        print(f"HTML length: {len(html)}")
        
        parser = KakaoParser(5)
        jobs = parser.parse(html)
        print(f'Found {len(jobs)} jobs in parser')
        
        for i, job in enumerate(jobs[:5]):
            print(f"[{i}] {job['company']} | {job['title']} | {job['deadline']} | {job['source_url']}")

if __name__ == "__main__":
    asyncio.run(test())

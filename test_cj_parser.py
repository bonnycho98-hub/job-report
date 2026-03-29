import asyncio
from backend.crawler.parsers.cj import CjParser
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        print("Navigating to CJ recruit list...")
        await page.goto('https://recruit.cj.net/recruit/ko/recruit/recruit/list.fo', wait_until='networkidle')
        html = await page.content()
        print(f"HTML length: {len(html)}")
        
        parser = CjParser(1)
        jobs = parser.parse(html)
        print(f'Found {len(jobs)} jobs in parser')
        
        # 추가 디버깅 
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        a_tags = soup.find_all('a')
        print(f"Total a tags: {len(a_tags)}")
        count = 0
        for i, a in enumerate(a_tags):
            href = a.get('href', '')
            if 'detail.fo' in href or 'bestDetail.fo' in href:
                count += 1
                print(f"[{i}] href={href}, text={a.text.strip()[:60]}")
        print(f"Total matching a tags: {count}")

if __name__ == "__main__":
    asyncio.run(test())

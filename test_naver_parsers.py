import asyncio
from backend.crawler.parsers.naver import NaverParser
from playwright.async_api import async_playwright

async def test_site(name, base_url, site_id):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        parser = NaverParser(site_id, base_url=base_url)
        print(f"[{name}] Navigating to {parser.target_url}...")
        await page.goto(parser.target_url, wait_until='networkidle')
        html = await page.content()
        print(f"[{name}] HTML length: {len(html)}")
        
        jobs = parser.parse(html)
        print(f'[{name}] Found {len(jobs)} jobs')
        
        for i, job in enumerate(jobs[:2]):
            print(f"[{name}] [{i}] {job['company']} | {job['title']} | {job['deadline']} | {job['source_url']}")
        await browser.close()

async def main():
    await test_site("Naver", "https://recruit.navercorp.com", 4)
    await test_site("Naver Cloud", "https://recruit.navercloudcorp.com", 6)
    await test_site("Naver Financial", "https://recruit.naverfincorp.com", 101)
    await test_site("Naver Webtoon", "https://recruit.webtoonscorp.com", 102)
    await test_site("SNOW", "https://recruit.snowcorp.com", 103)
    await test_site("Naver Labs", "https://recruit.naverlabs.com", 104)

if __name__ == "__main__":
    asyncio.run(main())

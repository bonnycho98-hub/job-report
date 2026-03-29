import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://recruit.cj.net/recruit/ko/recruit/recruit/list.fo", wait_until="networkidle")
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # 전체 HTML 중에서 채용 공고 부분으로 의심되는 부분을 찾습니다.
        # 보통 list 영역이나 board 영역입니다.
        list_items = soup.find_all('a')
        jobs = []
        for a in list_items:
            href = a.get('href', '')
            if 'detail.fo' in href or 'bestDetail.fo' in href: # detail.fo 가 공고 상세 링크
                jobs.append(str(a.parent))
                
        with open("cj_dom.html", "w", encoding="utf-8") as f:
            f.write("\n\n---\n\n".join(jobs))
        print(f"Extraction complete. Found {len(jobs)} potential job links.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())

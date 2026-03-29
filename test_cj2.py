import urllib.request
from bs4 import BeautifulSoup

url = "https://recruit.cj.net/recruit/ko/recruit/recruit/list.fo"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    html = response.read().decode('utf-8')

soup = BeautifulSoup(html, "html.parser")
jobs = soup.find_all('a')
results = []
for a in jobs:
    href = a.get('href', '')
    if 'detail.fo' in href or 'bestDetail.fo' in href:
        results.append(str(a.parent))

with open("cj_dom2.html", "w", encoding="utf-8") as f:
    f.write("\n\n---\n\n".join(results))
print(f"Found {len(results)} items.")

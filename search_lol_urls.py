import re
import sys
from curl_cffi import requests
from bs4 import BeautifulSoup

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

url = "https://www.oddsportal.com/esports/league-of-legends/"
r = requests.get(url, impersonate="chrome124", timeout=15)
print("Status:", r.status_code)
soup = BeautifulSoup(r.text, "html.parser")
links = soup.find_all("a", href=lambda h: h and "league-of-legends" in h)
print(f"找到 {len(links)} 個 LoL 相關連結:")
for l in links[:30]:
    txt = l.get_text(strip=True)
    href = l.get("href")
    if txt:
        print(f"  {txt} -> {href}")

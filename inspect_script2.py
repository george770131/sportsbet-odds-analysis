import sys
from curl_cffi import requests
from bs4 import BeautifulSoup

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

url = "https://www.sportsbet.com.au/betting/baseball/major-league-baseball"
r = requests.get(url, impersonate="chrome124", timeout=15)
soup = BeautifulSoup(r.text, "html.parser")
scripts = soup.find_all("script")

for idx, s in enumerate(scripts):
    txt = s.string or s.text or ""
    if "__APOLLO_STATE__" in txt:
        print(f"Script #{idx} Snippet (first 400 chars):")
        print(txt[:400])
        print("...")
        print(f"Script #{idx} End (last 200 chars):")
        print(txt[-200:])

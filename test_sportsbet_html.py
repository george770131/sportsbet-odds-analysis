import re
import json
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
print("Status:", r.status_code)

soup = BeautifulSoup(r.text, "html.parser")
scripts = soup.find_all("script")
print(f"找到 {len(scripts)} 個 script 標籤")

for idx, s in enumerate(scripts):
    txt = s.string or s.text or ""
    if "window.__INITIAL_STATE__" in txt or "__INITIAL_STATE__" in txt:
        print(f"Script #{idx} contains __INITIAL_STATE__, length: {len(txt)}")
    elif "window.__APOLLO_STATE__" in txt or "__APOLLO_STATE__" in txt:
        print(f"Script #{idx} contains __APOLLO_STATE__, length: {len(txt)}")
    elif "window.INITIAL_STATE" in txt:
        print(f"Script #{idx} contains INITIAL_STATE, length: {len(txt)}")
    elif "events" in txt and len(txt) > 500:
        print(f"Script #{idx} contains 'events' (len: {len(txt)}), snippet: {txt[:200]}")

# Also search for inline JSON state variables
matches = re.findall(r'window\.(\w+)\s*=\s*(\{.*?\});', r.text, re.DOTALL)
print(f"Regex window.VAR matches: {[m[0] for m in matches]}")

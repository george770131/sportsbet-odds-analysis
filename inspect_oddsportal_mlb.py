import json
import re
import sys
from curl_cffi import requests
from bs4 import BeautifulSoup

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

url = "https://www.oddsportal.com/baseball/usa/mlb/"
r = requests.get(url, impersonate="chrome124", timeout=15)
print(f"Status: {r.status_code}")

# Oddsportal provides an AJAX API for event odds:
# e.g. https://www.oddsportal.com/ajax-sport-country-tournament-archive/ / https://www.oddsportal.com/feed/...
soup = BeautifulSoup(r.text, "html.parser")
print("Title:", soup.title.string if soup.title else "")

# Let's find event links or team names in the HTML
links = soup.find_all("a", href=lambda h: h and "/baseball/usa/mlb/" in h)
print(f"Found {len(links)} MLB links")
for l in links[:15]:
    txt = l.get_text(strip=True)
    if txt and "-" in txt:
        print(f"Match: {txt} -> {l.get('href')}")

# Also check for embedded scripts or next data
for s in soup.find_all("script"):
    stxt = s.string or ""
    if "initialData" in stxt or "events" in stxt or "pageData" in stxt or "data" in stxt:
        print(f"Script with data len: {len(stxt)}, snippet: {stxt[:200]}")

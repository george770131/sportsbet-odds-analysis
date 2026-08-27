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

# Target: Sportsbet MLB page
url = "https://www.sportsbet.com.au/betting/baseball/major-league-baseball"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

print(f"[*] Connecting to Sportsbet directly: {url}")
try:
    r = requests.get(url, impersonate="chrome124", headers=headers, timeout=15)
    print(f"Status Code: {r.status_code}, Content Length: {len(r.text)}")
    
    if r.status_code == 200:
        # Search for preloaded state
        preloaded = re.findall(r'window\.__PRELOADED_STATE__\s*=\s*(\{.*?\});', r.text)
        if preloaded:
            print("Found window.__PRELOADED_STATE__!")
            data = json.loads(preloaded[0])
            with open("sportsbet_raw_preloaded.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("Saved to sportsbet_raw_preloaded.json")
        else:
            # Search for __NEXT_DATA__ or other script tags
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)
            print(f"Found {len(scripts)} scripts. Searching for odds/events...")
            for i, s in enumerate(scripts):
                if "events" in s or "market" in s or "outcomes" in s:
                    print(f"Script {i} matches! Length: {len(s)}")
                    with open(f"sportsbet_script_{i}.json", "w", encoding="utf-8") as f:
                        f.write(s[:5000])
except Exception as e:
    print(f"[!] Error: {e}")

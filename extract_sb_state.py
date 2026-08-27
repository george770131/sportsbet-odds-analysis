import json
import sys
from curl_cffi import requests

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

url = "https://www.sportsbet.com.au/betting/baseball/major-league-baseball"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

r = requests.get(url, impersonate="chrome124", headers=headers, timeout=15)
start_tag = "window.__PRELOADED_STATE__ = "
idx = r.text.find(start_tag)
print("Index of start_tag:", idx)

if idx != -1:
    raw_sub = r.text[idx + len(start_tag):]
    decoder = json.JSONDecoder()
    data, end_pos = decoder.raw_decode(raw_sub)
    print(f"Successfully decoded JSON! Length: {end_pos}")
    print("Top level keys:", list(data.keys()))
    
    with open("sportsbet_preloaded_full.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Saved to sportsbet_preloaded_full.json")

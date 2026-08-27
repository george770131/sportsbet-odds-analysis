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

# Extract window.__PRELOADED_STATE__
start_idx = r.text.find("window.__PRELOADED_STATE__ = ")
if start_idx != -1:
    start_idx += len("window.__PRELOADED_STATE__ = ")
    end_idx = r.text.find("\n\t\t\t\twindow.__APOLLO_STATE__", start_idx)
    if end_idx == -1:
        end_idx = r.text.find("window.__APOLLO_STATE__", start_idx)
    
    json_str = r.text[start_idx:end_idx].strip()
    state = json.loads(json_str)
    print("Preloaded State Top Keys:", list(state.keys()))
    
    for k in state.keys():
        val = state[k]
        if isinstance(val, dict):
            print(f"  Key [{k}] subkeys: {list(val.keys())[:10]}")
        elif isinstance(val, list):
            print(f"  Key [{k}] list len: {len(val)}")

# Also let's check what API calls the page makes or if there are competition IDs/class IDs
print("\n--- 檢查 Competition/Class IDs ---")
competition_ids = re.findall(r'/competition[s]?/(\d+)', r.text)
event_ids = re.findall(r'/event[s]?/(\d+)', r.text)
print("Found competition IDs:", set(competition_ids))
print("Found event IDs:", set(event_ids))

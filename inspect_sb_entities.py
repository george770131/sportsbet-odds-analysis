import json
import sys
from curl_cffi import requests

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

url = "https://www.sportsbet.com.au/betting/baseball/major-league-baseball"
r = requests.get(url, impersonate="chrome124", timeout=15)

start_idx = r.text.find("window.__PRELOADED_STATE__ = ") + len("window.__PRELOADED_STATE__ = ")
end_idx = r.text.find("\n\t\t\t\twindow.__APOLLO_STATE__", start_idx)
if end_idx == -1:
    end_idx = r.text.find("window.__APOLLO_STATE__", start_idx)

state = json.loads(r.text[start_idx:end_idx].strip())

print("--- Endpoints ---")
print(json.dumps(state.get("config", {}).get("endPoints", {}), indent=2))

print("\n--- Sportsbook entities keys ---")
sb = state.get("entities", {}).get("sportsbook", {})
print(list(sb.keys()))
for k, v in sb.items():
    if isinstance(v, dict):
        print(f"  [{k}] ({len(v)} items): keys = {list(v.keys())[:5]}")
    elif isinstance(v, list):
        print(f"  [{k}] (list len {len(v)})")

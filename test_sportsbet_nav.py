import json
import sys
from curl_cffi import requests

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

s = requests.Session()
# First visit main page to get cookies
init_r = s.get("https://www.sportsbet.com.au/", impersonate="chrome124", timeout=15)
print(f"Init status: {init_r.status_code}, cookies: {list(s.cookies.keys())}")

# Test NavHierarchy
nav_url = "https://www.sportsbet.com.au/apigw/sportsbook-sports/Sportsbook/Sports/NavHierarchy"
r = s.get(nav_url, impersonate="chrome124", timeout=15)
print(f"\nNavHierarchy Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"NavHierarchy data type: {type(data)}")
    if isinstance(data, list):
        print(f"Items count: {len(data)}")
        for item in data:
            name = item.get("name") or item.get("title")
            if name and any(k in name.lower() for k in ["baseball", "esports", "e-sports", "league"]):
                print(f"Match: {name}, ID: {item.get('id')}, ClassId: {item.get('classId')}")
                print(json.dumps(item, indent=2)[:500])
    elif isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")

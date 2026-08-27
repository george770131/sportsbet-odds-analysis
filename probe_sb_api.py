import json
import sys
from curl_cffi import requests

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Test common Sportsbet API endpoints
endpoints = [
    "https://www.sportsbet.com.au/apigw/sportsbook-view/v1/competitions/1000/events",
    "https://www.sportsbet.com.au/apigw/sportsbook-cq/v1/competition/1000/events",
    "https://www.sportsbet.com.au/apigw/sportsbook-core/sportsbook/v1/competitions/1000/events",
    "https://www.sportsbet.com.au/apigw/sportsbook-view/v1/sports/baseball/competitions",
    "https://www.sportsbet.com.au/apigw/sportsbook-cq/v1/sports/baseball/events",
    "https://www.sportsbet.com.au/apigw/sportsbook-view/v1/classes/baseball/events",
    "https://www.sportsbet.com.au/apigw/sportsbook-view/v1/competitions/major-league-baseball/events"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.sportsbet.com.au",
    "Referer": "https://www.sportsbet.com.au/betting/baseball/major-league-baseball"
}

for ep in endpoints:
    try:
        r = requests.get(ep, impersonate="chrome124", headers=headers, timeout=10)
        print(f"[{r.status_code}] {ep}")
        if r.status_code == 200:
            print(f"  Snippet: {r.text[:300]}")
    except Exception as e:
        print(f"[Err] {ep}: {e}")

import json
import sys
from curl_cffi import requests
from bs4 import BeautifulSoup

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

urls = {
    "MLB": "https://www.sportsbet.com.au/betting/baseball/major-league-baseball",
    "NPB": "https://www.sportsbet.com.au/betting/baseball/japan-npb",
    "CPBL": "https://www.sportsbet.com.au/betting/baseball/taiwan-cpbl",
    "LCK": "https://www.sportsbet.com.au/betting/esports/league-of-legends-champions-korea",
    "LPL": "https://www.sportsbet.com.au/betting/esports/league-of-legends-pro-league"
}

for league, url in urls.items():
    print(f"\n--- 測試 {league} ({url}) ---")
    try:
        r = requests.get(url, impersonate="chrome124", timeout=15)
        print(f"Status Code: {r.status_code}, Content Length: {len(r.text)}")
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            next_data = soup.find("script", id="__NEXT_DATA__")
            if next_data and next_data.string:
                data = json.loads(next_data.string)
                page_props = data.get("props", {}).get("pageProps", {})
                print(f"PageProps keys: {list(page_props.keys())}")
                
                # Check for events, matches, markets
                events = page_props.get("events") or page_props.get("initialData", {}).get("events") or page_props.get("competition", {}).get("events")
                if events:
                    print(f"找到 {len(events)} 場賽事 (events)！")
                    sample = events[0]
                    print(f"賽事範例: {sample.get('name') or sample.get('title')}")
                else:
                    # Search entire JSON for events
                    print("深入搜尋 JSON 結構...")
                    def find_keys(obj, target_key, max_depth=4, current_depth=0):
                        if current_depth > max_depth or not isinstance(obj, (dict, list)):
                            return []
                        found = []
                        if isinstance(obj, dict):
                            for k, v in obj.items():
                                if target_key in k.lower():
                                    found.append((k, type(v), len(v) if isinstance(v, (list, dict)) else v))
                                found.extend(find_keys(v, target_key, max_depth, current_depth + 1))
                        elif isinstance(obj, list):
                            for item in obj[:5]:
                                found.extend(find_keys(item, target_key, max_depth, current_depth + 1))
                        return found
                    
                    matches_found = find_keys(page_props, "event")
                    print(f"相關 event 欄位: {matches_found[:10]}")
            else:
                print(f"頁面文字片段: {r.text[:500]}")
        else:
            print(f"連線未成功: {r.status_code}")
    except Exception as e:
        print(f"連線失敗: {e}")

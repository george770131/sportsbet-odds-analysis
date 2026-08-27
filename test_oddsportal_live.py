import json
import sys
from curl_cffi import requests
from bs4 import BeautifulSoup

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

oddsportal_urls = {
    "MLB": "https://www.oddsportal.com/baseball/usa/mlb/",
    "NPB": "https://www.oddsportal.com/baseball/japan/npb/",
    "CPBL": "https://www.oddsportal.com/baseball/taiwan/cpbl/",
    "LCK": "https://www.oddsportal.com/esports/south-korea/league-of-legends-champions-korea/",
    "LPL": "https://www.oddsportal.com/esports/china/league-of-legends-pro-league/"
}

for name, url in oddsportal_urls.items():
    print(f"\n--- 測試 Oddsportal {name} ({url}) ---")
    try:
        r = requests.get(url, impersonate="chrome124", timeout=15)
        print(f"Status: {r.status_code}, Length: {len(r.text)}")
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.string if soup.title else "No Title"
            print(f"頁面標題: {title}")
            # 尋找賽事列表
            event_rows = soup.find_all("div", class_=lambda c: c and ("eventRow" in c or "flex" in c or "border-b" in c))
            print(f"找到 HTML 元素: {len(event_rows)} 個")
            # 檢查是否有 next_data
            next_data = soup.find("script", id="__NEXT_DATA__")
            if next_data and next_data.string:
                data = json.loads(next_data.string)
                print(f"Next Data 包含 keys: {list(data.keys())}")
                page_data = data.get("props", {}).get("pageProps", {})
                print(f"PageProps keys: {list(page_data.keys())}")
    except Exception as e:
        print(f"連線失敗: {e}")

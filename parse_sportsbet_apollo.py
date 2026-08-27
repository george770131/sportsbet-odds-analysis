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

# 提取 window.__APOLLO_STATE__ = { ... };
match = re.search(r'window\.__APOLLO_STATE__\s*=\s*({.+?});\s*</script>', r.text, re.DOTALL)
if not match:
    # 嘗試另一種匹配模式
    match = re.search(r'__APOLLO_STATE__\s*=\s*({.+?});', r.text)

if match:
    apollo_json = json.loads(match.group(1))
    print(f"成功解析 Apollo State！鍵值數量: {len(apollo_json)}")
    
    # 遍歷尋找 Event, Market, Outcome
    events = {}
    markets = {}
    outcomes = {}
    
    for k, v in apollo_json.items():
        if isinstance(v, dict):
            type_name = v.get("__typename")
            if type_name == "Event" or k.startswith("Event:"):
                events[k] = v
            elif type_name == "Market" or k.startswith("Market:"):
                markets[k] = v
            elif type_name in ["Outcome", "Price", "Selection"] or k.startswith("Outcome:") or k.startswith("Selection:"):
                outcomes[k] = v

    print(f"找到 Event 實例: {len(events)} 個")
    print(f"找到 Market 實例: {len(markets)} 個")
    print(f"找到 Outcome/Selection 實例: {len(outcomes)} 個")

    # 列印前 5 場賽事詳情
    for k, ev in list(events.items())[:5]:
        print("\n-------------------------")
        print(f"Event ID: {k}")
        print(f"名稱: {ev.get('name') or ev.get('title')}")
        print(f"開賽時間: {ev.get('startTime') or ev.get('advertisedStartTime') or ev.get('date')}")
        print(f"完整欄位: {list(ev.keys())}")
        
        # 尋找其關聯之 markets
        market_refs = ev.get("markets") or []
        print(f"Markets count: {len(market_refs)}")
        if isinstance(market_refs, list):
            for m_ref in market_refs[:3]:
                m_key = m_ref.get("id") if isinstance(m_ref, dict) else str(m_ref)
                if m_key in markets:
                    m = markets[m_key]
                    print(f"  Market: {m.get('name')}, Type: {m.get('marketType')}")
else:
    print("未找到 __APOLLO_STATE__ 正則匹配")

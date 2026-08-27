import json
import re
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
print(f"Fetch Sportsbet MLB: {r.status_code}, Length: {len(r.text)}")

# Extract window.__PRELOADED_STATE__
match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(\{.*?\});\s*</script>', r.text, re.DOTALL)
if match:
    raw_json = match.group(1)
    print(f"Extracted PRELOADED_STATE JSON string length: {len(raw_json)}")
    data = json.loads(raw_json)
    
    # Sportsbet state usually has entities -> events, markets, outcomes
    entities = data.get("entities", {})
    print("Entities keys:", list(entities.keys()))
    
    events = entities.get("events", {})
    markets = entities.get("markets", {})
    outcomes = entities.get("outcomes", {})
    
    print(f"Total events found: {len(events)}")
    print(f"Total markets found: {len(markets)}")
    print(f"Total outcomes found: {len(outcomes)}")
    
    for ev_id, ev in list(events.items())[:15]:
        ev_name = ev.get("name", "")
        ev_time = ev.get("startTime", "")
        ev_markets = ev.get("markets", [])
        print(f"\n[Event {ev_id}] {ev_name} @ {ev_time}")
        for m_id in ev_markets:
            m = markets.get(str(m_id), {})
            m_name = m.get("name", "")
            m_type = m.get("type", "")
            m_outcomes = m.get("outcomes", [])
            print(f"  Market ({m_name} / {m_type}):")
            for oc_id in m_outcomes:
                oc = outcomes.get(str(oc_id), {})
                oc_name = oc.get("name", "")
                oc_price = oc.get("price", {})
                dec_price = oc_price.get("decimal", "")
                handicap = oc.get("handicap", "")
                print(f"    Outcome: {oc_name} | Decimal Odds: {dec_price} | Handicap: {handicap}")
else:
    print("[!] window.__PRELOADED_STATE__ not found in regex")

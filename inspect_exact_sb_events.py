import json
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

with open("sportsbet_preloaded_full.json", "r", encoding="utf-8") as f:
    data = json.load(f)

entities = data.get("entities", {})
print("Entities keys:", list(entities.keys()))

events = entities.get("events", {})
markets = entities.get("markets", {})
outcomes = entities.get("outcomes", {})

print(f"\nTotal Events: {len(events)}")
print(f"Total Markets: {len(markets)}")
print(f"Total Outcomes: {len(outcomes)}")

for ev_id, ev in events.items():
    name = ev.get("name", "")
    start_t = ev.get("startTime", "")
    comp_name = ev.get("competitionName", "")
    print(f"\n=======================================================")
    print(f"賽事 [{comp_name}] {name} (ID: {ev_id}) 開賽時間: {start_t}")
    
    # 尋找該賽事的所有盤口
    ev_market_ids = ev.get("markets", [])
    for m_id in ev_market_ids:
        m = markets.get(str(m_id), {})
        m_name = m.get("name", "")
        m_type = m.get("type", "")
        print(f"  -> 盤口: {m_name} ({m_type})")
        
        # 尋找該盤口的所有賠率結果
        for oc_id in m.get("outcomes", []):
            oc = outcomes.get(str(oc_id), {})
            oc_name = oc.get("name", "")
            oc_price = oc.get("price", {})
            dec_odds = oc_price.get("decimal", "")
            handicap = oc.get("handicap", "")
            print(f"       * {oc_name} | 賠率: {dec_odds} | 讓分/基準: {handicap}")

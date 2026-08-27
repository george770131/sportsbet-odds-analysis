import json

with open("sportsbet_preloaded_full.json", "r", encoding="utf-8") as f:
    data = json.load(f)

sb = data.get("entities", {}).get("sportsbook", {})
print("Sportsbook keys:", list(sb.keys()))

events = sb.get("events", {})
markets = sb.get("markets", {})
outcomes = sb.get("outcomes", {})

print(f"\nTotal Events in sportsbook: {len(events)}")
print(f"Total Markets in sportsbook: {len(markets)}")
print(f"Total Outcomes in sportsbook: {len(outcomes)}")

for ev_id, ev in list(events.items())[:20]:
    name = ev.get("name", "")
    start_t = ev.get("startTime", "")
    comp_name = ev.get("competitionName", "")
    print(f"\n=======================================================")
    print(f"賽事: {name} (ID: {ev_id}) | 開賽: {start_t}")
    
    # 尋找該賽事的所有盤口
    ev_market_ids = ev.get("markets", [])
    for m_id in ev_market_ids:
        m = markets.get(str(m_id), {})
        m_name = m.get("name", "")
        m_type = m.get("type", "")
        print(f"  -> 盤口: {m_name} ({m_type})")
        
        for oc_id in m.get("outcomes", []):
            oc = outcomes.get(str(oc_id), {})
            oc_name = oc.get("name", "")
            oc_price = oc.get("price", {})
            dec_odds = oc_price.get("winDecimal", oc_price.get("decimal", ""))
            handicap = oc.get("handicap", "")
            print(f"       * {oc_name} | 賠率: {dec_odds} | 讓分/基準: {handicap}")

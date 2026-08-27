import re
import json
import sys
from curl_cffi import requests

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def parse_oddsportal_page(sport: str, league: str, url: str):
    print(f"\n==========================================")
    print(f"正在解析 {league} 真實賽事: {url}")
    print(f"==========================================")
    
    r = requests.get(url, impersonate="chrome124", timeout=15)
    if r.status_code != 200:
        print(f"[!] 請求失敗: {r.status_code}")
        return []

    # 提取所有 Next.js RSC chunks
    chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)', r.text)
    full_payload = "".join(chunks).encode('utf-8').decode('unicode_escape')

    # 尋找匹配如 "Team A - Team B 27 Aug 2026, 01:15:00 at Stadium"
    pattern = r'([A-Za-z0-9\.\s]+)\s*-\s*([A-Za-z0-9\.\s]+)\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4},\s+\d{2}:\d{2}:\d{2})'
    found_matches = re.findall(pattern, full_payload)
    
    # 尋找直接對戰組合
    direct_pattern = r'href=[\\]*"/([^"]+/[^"]+/[^"]+/([a-z0-9\-]+)-([a-z0-9\-]+)-([a-zA-Z0-9]+)/)"'
    slug_matches = re.findall(direct_pattern, full_payload)
    
    print(f"找到正規賽事排程: {len(found_matches)} 場")
    events = []
    
    seen_keys = set()
    for h, a, t in found_matches:
        home = h.strip()
        away = a.strip()
        key = f"{home}_{away}_{t}"
        if key not in seen_keys:
            seen_keys.add(key)
            events.append({
                "league": league,
                "sport": sport,
                "home_team": home,
                "away_team": away,
                "start_time": t,
                "raw": f"{home} vs {away} @ {t}"
            })
            print(f"  [賽事] {home} vs {away} | 開賽: {t}")

    print(f"找到賽事 Slugs: {len(slug_matches)} 個")
    for full_slug, s_h, s_a, eid in slug_matches[:10]:
        print(f"  Slug: {s_h} vs {s_a} (ID: {eid}) -> {full_slug}")

    return events

if __name__ == "__main__":
    parse_oddsportal_page("baseball", "MLB", "https://www.oddsportal.com/baseball/usa/mlb/")
    parse_oddsportal_page("baseball", "NPB", "https://www.oddsportal.com/baseball/japan/npb/")
    parse_oddsportal_page("baseball", "CPBL", "https://www.oddsportal.com/baseball/taiwan/cpbl/")
    parse_oddsportal_page("esports", "LCK", "https://www.oddsportal.com/esports/south-korea/league-of-legends-champions-korea/")
    parse_oddsportal_page("esports", "LPL", "https://www.oddsportal.com/esports/china/league-of-legends-pro-league/")

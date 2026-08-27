import re
import sys
from curl_cffi import requests

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

url = "https://www.oddsportal.com/baseball/usa/mlb/"
r = requests.get(url, impersonate="chrome124", timeout=15)

chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)', r.text)
full_payload = "".join(chunks).encode('utf-8').decode('unicode_escape')

# 尋找形如 "Team A - Team B" 的對戰組合
match_titles = re.findall(r'([A-Za-z0-9\.\s]+)\s*-\s*([A-Za-z0-9\.\s]+)', full_payload)
print(f"找到潛在對戰組合: {len(match_titles)} 組")

# 尋找賽事物件 (包含 URL, slug, event ID, time, odds)
event_blocks = re.findall(r'\{[^{}]*?"name"\s*:\s*"([A-Za-z0-9\.\s]+ - [A-Za-z0-9\.\s]+)"[^{}]*?\}', full_payload)
print(f"找到 Event JSON 區塊: {len(event_blocks)}")
for b in event_blocks[:10]:
    print("Block:", b)

# 搜尋所有包含 " - " 的字串
all_matches = re.findall(r'"([^"]+ - [^"]+)"', full_payload)
print(f"\n所有 ' - ' 配對賽事 ({len(all_matches)} 個):")
for m in set(all_matches):
    print("  ->", m)

# 搜尋這幾場賽事附近的賠率數據 (浮點數 1.xx ~ 3.xx)
print("\n搜尋相關賠率區塊...")
odds_snippets = re.findall(r'"(?:odds|price|avgOdds|value|home|away)":\s*"?([0-9]\.[0-9]{2,3})"?', full_payload)
print(f"找到相關賠率浮點數: {odds_snippets[:20]}")

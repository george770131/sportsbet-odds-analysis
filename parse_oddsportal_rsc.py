import json
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

# 搜尋 self.__next_f.push([1, "..."])
chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)', r.text)
full_payload = "".join(chunks).encode('utf-8').decode('unicode_escape')

print(f"RSC Payload 長度: {len(full_payload)}")

# 尋找隊伍名稱與賠率資料
# 例如 "homeTeam", "awayTeam", "odds", "event"
print("搜尋賽事與隊伍...")
matches = re.findall(r'"homeParticipant"\s*:\s*\{"name"\s*:\s*"([^"]+)".*?"awayParticipant"\s*:\s*\{"name"\s*:\s*"([^"]+)"', full_payload)
print(f"找到賽事配對: {len(matches)} 場")
for h, a in matches:
    print(f"  {h} vs {a}")

# 如果是另一種結構
if not matches:
    # 搜尋 "homeTeamName" 或 "homeTeam" 或隊伍名字
    team_matches = re.findall(r'"name"\s*:\s*"([A-Za-z0-9\s\.\-]+)"', full_payload)
    print(f"找到名稱字段: {len(team_matches)} 個: {team_matches[:20]}")
    
    # 搜尋賠率格式如 "1.85", "2.10"
    odds_matches = re.findall(r'"odds"\s*:\s*"([0-9\.]+)"', full_payload)
    print(f"找到 odds: {odds_matches[:10]}")

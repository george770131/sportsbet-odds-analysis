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

url = "https://www.oddsportal.com/baseball/usa/mlb/"
r = requests.get(url, impersonate="chrome124", timeout=15)

chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)', r.text)
full_payload = "".join(chunks).encode('utf-8').decode('unicode_escape')

print(f"Payload length: {len(full_payload)}")

# Find where team names appear and inspect surrounding text
target_teams = ["Los Angeles Angels", "Detroit Tigers", "Atlanta Braves", "New York Yankees"]
for team in target_teams:
    idx = full_payload.find(team)
    if idx != -1:
        print(f"\n==================== {team} 周圍 1000 字元 ====================")
        snippet = full_payload[max(0, idx - 200): min(len(full_payload), idx + 1000)]
        print(snippet)

# Also let's inspect the JSON structure if there is structured event object
event_objects = re.findall(r'\{[^{}]*?"name"\s*:\s*"[^"]*?Angels[^"]*?"[^{}]*?\}', full_payload)
print(f"\nEvent objects containing Angels: {len(event_objects)}")
for obj in event_objects:
    print(obj)

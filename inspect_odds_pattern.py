import re
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
print(f"Status: {r.status_code}")

chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)', r.text)
full_payload = "".join(chunks).encode('utf-8').decode('unicode_escape')

# Oddsportal table row format in React components:
# Rows contain [HomeTeam, AwayTeam, Odds1, Odds2, OddsX/OverUnder]
# Let's search for patterns where match names are followed by numbers or odds
lines = full_payload.split("\n")
print(f"Payload has {len(lines)} lines")

# Let's search for odds numbers (e.g. 1.50 ~ 3.50)
odds_matches = re.findall(r'(\d\.\d{2})', full_payload)
print(f"Total decimal numbers like X.XX: {len(odds_matches)}")
print(f"Sample decimal numbers: {odds_matches[:30]}")

# Let's inspect chunks where decimal odds appear
for m in re.finditer(r'([A-Za-z\.\s]+ - [A-Za-z\.\s]+)', full_payload):
    start = m.start()
    name = m.group(1)
    if "Baseball" not in name and "Odds" not in name and len(name) < 60:
        surrounding = full_payload[start: start + 400]
        odds_found = re.findall(r'\b([1-9]\.[0-9]{2})\b', surrounding)
        print(f"Match: {name.strip()} -> Odds nearby: {odds_found[:4]}")

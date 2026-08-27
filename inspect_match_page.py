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

# Test match: Detroit Tigers vs Tampa Bay Rays
# Event URL: https://www.oddsportal.com/baseball/usa/mlb/detroit-tigers-tampa-bay-rays-UHDyCOWg/
# Or https://www.oddsportal.com/feed/match/1-1-UHDyCOWg-1-2-yba36.dat
match_urls = [
    "https://www.oddsportal.com/baseball/usa/mlb/detroit-tigers-tampa-bay-rays-UHDyCOWg/",
    "https://www.oddsportal.com/baseball/usa/mlb/atlanta-braves-los-angeles-dodgers-nc2lnvh2/",
    "https://www.oddsportal.com/baseball/usa/mlb/houston-astros-new-york-yankees-82mq8LEL/"
]

for url in match_urls:
    print(f"\n==========================================")
    print(f"Fetching Match: {url}")
    r = requests.get(url, impersonate="chrome124", timeout=15)
    print(f"Status: {r.status_code}, Length: {len(r.text)}")
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        print("Page Title:", soup.title.string if soup.title else "")
        
        # Check Next.js payload for bookmaker odds table
        chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)', r.text)
        full_payload = "".join(chunks).encode('utf-8').decode('unicode_escape')
        
        # Search for bookmaker names & odds
        bookies = re.findall(r'"bookmakerName"\s*:\s*"([^"]+)"', full_payload)
        print(f"Bookmakers found: {set(bookies)}")
        
        odds_list = re.findall(r'"odds"\s*:\s*"?([0-9\.]+)"?', full_payload)
        print(f"Odds numbers found: {odds_list[:15]}")
        
        # Search for text odds in table cells
        odds_cells = soup.find_all(lambda tag: tag.name in ["p", "span", "div", "a"] and re.match(r'^[1-9]\.[0-9]{2}$', tag.get_text(strip=True)))
        print(f"HTML Odds cells found: {[c.get_text(strip=True) for c in odds_cells[:20]]}")

import requests
import re
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8",
    "Referer": "https://www.oddsportal.com/"
}

url = "https://www.oddsportal.com/baseball/taiwan/cpbl/"
r = requests.get(url, headers=headers, timeout=15)
print("Status Code:", r.status_code)
print("Content Length:", len(r.text))

# Search for any embedded JSON data or team strings
keywords = ["Lions", "Monkeys", "Brothers", "Dragons", "Guardians", "Hawks", "CPBL", "baseball", "events"]
for kw in keywords:
    matches = re.findall(rf'.{{0,50}}{kw}.{{0,50}}', r.text, re.IGNORECASE)
    print(f"Keyword '{kw}' matches count: {len(matches)}")
    if matches:
        print("Sample:", matches[:2])

# Search for next.js f.push chunks
f_pushes = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', r.text)
print("f.push chunks count:", len(f_pushes))
for i, chunk in enumerate(f_pushes):
    if "baseball" in chunk.lower() or "cpbl" in chunk.lower() or "taiwan" in chunk.lower():
        print(f"Chunk {i} (len {len(chunk)}): {chunk[:300]}")

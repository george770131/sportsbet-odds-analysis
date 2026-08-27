import json
import re
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

with open("sportsbet_script_2.json", "r", encoding="utf-8") as f:
    raw = f.read()

print("Script 2 length:", len(raw))
print("First 500 chars:", raw[:500])

# Let's inspect if it's JSON or JavaScript variable assignment
# e.g., window.__APOLLO_STATE__ or __INITIAL_STATE__
if "window." in raw:
    match = re.search(r'window\.([A-Za-z0-9_]+)\s*=\s*', raw)
    if match:
        var_name = match.group(1)
        print(f"Assigned to variable: window.{var_name}")

# Search for match names, e.g. Tigers, Rays, Yankees, Dodgers
for team in ["Tigers", "Rays", "Yankees", "Dodgers", "Angels"]:
    matches = [m.start() for m in re.finditer(team, raw, re.IGNORECASE)]
    print(f"Found '{team}' at indices: {matches[:5]}")
    if matches:
        idx = matches[0]
        snippet = raw[max(0, idx - 100): min(len(raw), idx + 300)]
        print(f"  Snippet: {snippet}\n")

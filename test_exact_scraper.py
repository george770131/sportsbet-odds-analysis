import asyncio
import re
import sys
from playwright.async_api import async_playwright
import config

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

LEAGUE_URLS = {
    "MLB": ("baseball", "https://www.oddsportal.com/baseball/usa/mlb/"),
    "NPB": ("baseball", "https://www.oddsportal.com/baseball/japan/npb/"),
    "CPBL": ("baseball", "https://www.oddsportal.com/baseball/taiwan/cpbl/"),
    "LCK": ("esports", "https://www.oddsportal.com/esports/league-of-legends/league-of-legends-lck/"),
    "LPL": ("esports", "https://www.oddsportal.com/esports/league-of-legends/league-of-legends-lpl/")
}

async def extract_exact_league_odds(page, league, sport, url):
    print(f"\n==========================================")
    print(f"正在抓取 {league} 實時真實賠率: {url}")
    print(f"==========================================")
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"[!] 載入超時或錯誤: {e}")

    # 提取頁面文字行
    text = await page.evaluate("() => document.body.innerText")
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    matches = []
    i = 0
    while i < len(lines) - 4:
        # 尋找 "HomeTeam\n-\nAwayTeam\nOdds1\nOdds2" 的結構
        if lines[i+1] == "-" and i+4 < len(lines):
            home = lines[i]
            away = lines[i+2]
            
            # 檢查後續是否為賠率浮點數 (1.01 ~ 15.00)
            val1 = lines[i+3]
            val2 = lines[i+4]
            
            # 濾除比分 (例如 Finished 賽事的中間行)
            odds_pattern = r'^[1-9]\d*(\.\d{2})$'
            
            o1, o2 = None, None
            # 檢查 val1, val2 是否為賠率
            if re.match(odds_pattern, val1) and re.match(odds_pattern, val2):
                o1 = float(val1)
                o2 = float(val2)
            elif i+5 < len(lines) and re.match(odds_pattern, lines[i+4]) and re.match(odds_pattern, lines[i+5]):
                o1 = float(lines[i+4])
                o2 = float(lines[i+5])
                
            if o1 and o2 and "Baseball" not in home and "Odds" not in home and len(home) < 40 and len(away) < 40:
                matches.append({
                    "league": league,
                    "sport": sport,
                    "home_team": home,
                    "away_team": away,
                    "home_odds": o1,
                    "away_odds": o2
                })
                print(f"  [✓] {home} vs {away} | 主勝賠率: {o1} | 客勝賠率: {o2}")
                i += 4
                continue
        i += 1
        
    print(f"總共成功抓取到 {len(matches)} 場包含精確賠率之賽事！")
    return matches

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        
        for league, (sport, url) in LEAGUE_URLS.items():
            await extract_exact_league_odds(page, league, sport, url)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

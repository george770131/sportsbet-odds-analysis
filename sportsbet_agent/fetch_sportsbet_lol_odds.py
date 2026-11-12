#!/usr/bin/env python3
"""
Sportsbet 英雄聯盟世界大賽 (LoL Worlds) 即時盤口爬取器 (fetch_sportsbet_lol_odds.py)
-----------------------------------------------------------------------------
功能：
- 透過本地 Surfshark 澳洲代理 (http://127.0.0.1:8888) 訪問 Sportsbet
- 搭載 Playwright Stealth 反爬引擎
- 自動抓取英雄聯盟世界大賽 (LoL - World Championship) 的所有對戰與獨贏盤口 (Money Line)
- 輸出結構化資料與 Telegram 格式化報告
- 截圖存證至 sportsbet_lol_odds.png
-----------------------------------------------------------------------------
"""

import sys
import re
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

try:
    from .proxy_config import get_active_proxy
except ImportError:
    from proxy_config import get_active_proxy

BASE_DIR = Path(__file__).resolve().parent
SCREENSHOT_FILE = BASE_DIR / "sportsbet_lol_odds.png"

def fetch_lol_world_championship_odds() -> list[dict]:
    matches_data = []
    active_proxy = get_active_proxy()

    with sync_playwright() as p:
        launch_kwargs = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-setuid-sandbox", "--lang=en-AU,en"]
        }
        if active_proxy:
            launch_kwargs["proxy"] = {"server": active_proxy}
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="en-AU",
            timezone_id="Australia/Melbourne"
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        url = "https://www.sportsbet.com.au/betting/e-sports/lol-world-championship"
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3500)

        body_text = page.inner_text("main") if page.query_selector("main") else page.inner_text("body")
        lines = [l.strip() for l in body_text.split("\n") if l.strip()]

        current_date = "Saturday, 24 Oct"
        for i, line in enumerate(lines):
            if re.match(r'^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Today|Tomorrow)', line):
                current_date = line
                continue

            # 匹配時間與對戰，例如: "04:00" \n "1 Market" \n "Gen.G v Invictus Gaming" \n "Gen.G" \n "1.17" \n "Invictus Gaming" \n "4.90"
            if re.match(r'^\d{2}:\d{2}$', line) and i + 6 < len(lines):
                match_time = f"{current_date} {line} (AEDT)"
                
                # 往後探索對戰塊
                sub_slice = lines[i:i+15]
                chunk = "\n".join(sub_slice)

                m = re.search(
                    r'(\d{2}:\d{2})\n(?:1 Market|\d+ Markets)?\n([^\n]+?)\s*v\s*([^\n]+?)\n([^\n]+?)\n([\d\.]+)\n([^\n]+?)\n([\d\.]+)',
                    chunk
                )
                if m:
                    time_val = m.group(1)
                    team1 = m.group(2).strip()
                    team2 = m.group(3).strip()
                    odd_team1 = m.group(4).strip()
                    odd_val1 = m.group(5).strip()
                    odd_team2 = m.group(6).strip()
                    odd_val2 = m.group(7).strip()

                    # 計算台灣時間 (AEDT UTC+11 比台灣 UTC+8 快 3 小時)
                    try:
                        h, mn = map(int, time_val.split(":"))
                        tw_h = (h - 3) % 24
                        tw_time_str = f"台灣時間 {tw_h:02d}:{mn:02d}"
                    except Exception:
                        tw_time_str = ""

                    matches_data.append({
                        "tournament": "LoL - World Championship (英雄聯盟世界大賽)",
                        "time_aedt": f"{current_date} {time_val} AEDT",
                        "time_tw": tw_time_str,
                        "matchup": f"{team1} vs {team2}",
                        "team1": team1,
                        "odds1": odd_val1,
                        "team2": team2,
                        "odds2": odd_val2
                    })

        page.screenshot(path=str(SCREENSHOT_FILE))
        browser.close()

    return matches_data


def format_lol_odds_report(matches: list) -> str:
    """產出 Telegram 專業排版之英雄聯盟世界大賽獨贏盤口報告"""
    if not matches:
        return (
            "🎮 <b>【Sportsbet 英雄聯盟世界大賽 (LoL Worlds) 盤口】</b> <i>(澳洲墨爾本節點直連)</i>\n\n"
            "目前線上暫查無開盤賽事，請稍後再試。"
        )

    lines = [
        "🎮 <b>【Sportsbet 英雄聯盟世界大賽 (LoL Worlds) 獨贏盤口】</b> <i>(澳洲墨爾本直連)</i>\n"
    ]

    for i, m in enumerate(matches, 1):
        matchup = m.get("matchup", "")
        time_tw = m.get("time_tw", "")
        time_aedt = m.get("time_aedt", "")
        t1 = m.get("team1", "")
        o1 = m.get("odds1", "")
        t2 = m.get("team2", "")
        o2 = m.get("odds2", "")

        lines.append(
            f"<b>{i}. ⚔️ {matchup}</b>\n"
            f"   • <b>開賽時間</b>：<code>{time_tw}</code> <i>({time_aedt})</i>\n"
            f"   • <b>獨贏盤 (Match Winner) 賠率</b>：\n"
            f"     - <b>{t1}</b>：<code>{o1}</code>\n"
            f"     - <b>{t2}</b>：<code>{o2}</code>"
        )

    taiwan_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    lines.append(f"\n⏱️ <i>情資採集時間：{taiwan_now} (台灣時間) ｜ 代理出口：Surfshark Melbourne AU</i>")
    return "\n\n".join(lines)


if __name__ == "__main__":
    matches = fetch_lol_world_championship_odds()
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        print(format_lol_odds_report(matches))

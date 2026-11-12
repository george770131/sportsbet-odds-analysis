#!/usr/bin/env python3
"""
Sportsbet 棒球即時盤口爬取器 (fetch_sportsbet_baseball_odds.py)
-----------------------------------------------------------------------------
功能：
- 透過本地 Surfshark 澳洲代理 (http://127.0.0.1:8888) 訪問 Sportsbet
- 搭載 Playwright Stealth 反爬引擎
- 自動抓取目前「即時滾球盤 (LIVE)」與「近期賽事 (Upcoming)」的棒球獨贏盤口 (Money Line)
- 輸出結構化資料與截圖存證 (sportsbet_baseball_odds.png)
- 支援產出 Telegram 格式化報告 (format_baseball_odds_report)
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
SCREENSHOT_FILE = BASE_DIR / "sportsbet_baseball_odds.png"

def clean_team_name(name: str) -> str:
    """清理隊名字串"""
    lines = [l.strip() for l in name.strip().split("\n") if l.strip()]
    return lines[-1] if lines else name.strip()

def fetch_baseball_odds() -> list[dict]:
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

        base_url = "https://www.sportsbet.com.au/betting/baseball"
        page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        # 1. 抓取即時滾球 (Bet Live)
        live_btn = page.query_selector('button:has-text("Bet Live"), [role="tab"]:has-text("Bet Live")')
        if live_btn:
            live_btn.click()
            page.wait_for_timeout(2000)

            body_text = page.inner_text("main") if page.query_selector("main") else page.inner_text("body")
            lines = [l.strip() for l in body_text.split("\n") if l.strip()]

            for i, line in enumerate(lines):
                if line == "LIVE" and i + 10 < len(lines):
                    status_info = lines[i+1] # e.g. 6th Innings
                    league_info = lines[i+3] if (i+2 < len(lines) and lines[i+2] == "|") else lines[i+2]

                    sub_slice = lines[i:i+25]
                    match_chunk = "\n".join(sub_slice)
                    m = re.search(r'([A-Za-z0-9\s]+)\s*@\s*\n\s*([A-Za-z0-9\s]+)\n\s*(\d+)\s*\n\s*(\d+)\s*\n\s*([A-Za-z0-9\s]+)\s*\n\s*([\d\.]+)\s*\n\s*([A-Za-z0-9\s]+)\s*\n\s*([\d\.]+)', match_chunk)
                    if m:
                        away_team = clean_team_name(m.group(1))
                        home_team = m.group(2).strip().split("\n")[0].strip()
                        away_score = m.group(3).strip()
                        home_score = m.group(4).strip()
                        team1 = clean_team_name(m.group(5))
                        odds1 = m.group(6).strip()
                        team2 = clean_team_name(m.group(7))
                        odds2 = m.group(8).strip()

                        matches_data.append({
                            "type": "🔥 即時滾球進行中 (LIVE In-Play)",
                            "league": league_info,
                            "status": status_info,
                            "matchup": f"{away_team} @ {home_team}",
                            "score": f"{away_score} - {home_score}",
                            "moneyline": [
                                {"team": team1, "odds": odds1},
                                {"team": team2, "odds": odds2}
                            ]
                        })

        # 2. 抓取近期賽事 (Upcoming)
        upcoming_btn = page.query_selector('button:has-text("Upcoming"), [role="tab"]:has-text("Upcoming")')
        if upcoming_btn:
            upcoming_btn.click()
            page.wait_for_timeout(2000)

            body_text = page.inner_text("main") if page.query_selector("main") else page.inner_text("body")
            lines = [l.strip() for l in body_text.split("\n") if l.strip()]

            for i, line in enumerate(lines):
                if re.match(r'^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Today|Tomorrow)', line) and i + 10 < len(lines):
                    date_str = line
                    time_line = lines[i+1] if i+1 < len(lines) else ""
                    m_time = re.search(r'(\d{1,2}:\d{2})\s*\|\s*([^\n]+)', time_line)
                    if m_time:
                        match_time = f"{date_str} {m_time.group(1)} (AEDT)"
                        league_name = m_time.group(2).strip()

                        sub_slice = lines[i:i+20]
                        chunk = "\n".join(sub_slice)
                        m_teams = re.search(r'([A-Za-z0-9\s\(\)\.\-]+)\s*@\s*([A-Za-z0-9\s\(\)\.\-]+)\n\s*([A-Za-z0-9\s\(\)\.\-]+)\s*\n\s*([\d\.]+)\s*\n\s*([A-Za-z0-9\s\(\)\.\-]+)\s*\n\s*([\d\.]+)', chunk)
                        if m_teams:
                            away_raw = m_teams.group(1)
                            home_raw = m_teams.group(2)
                            away_team = clean_team_name(away_raw)
                            home_team = home_raw.strip().split("\n")[0].strip()

                            matches_data.append({
                                "type": "📅 近期即將開打 (Upcoming Pre-Match)",
                                "league": league_name,
                                "status": match_time,
                                "matchup": f"{away_team} @ {home_team}",
                                "score": "-",
                                "moneyline": [
                                    {"team": clean_team_name(m_teams.group(3)), "odds": m_teams.group(4).strip()},
                                    {"team": clean_team_name(m_teams.group(5)), "odds": m_teams.group(6).strip()}
                                ]
                            })

        page.screenshot(path=str(SCREENSHOT_FILE))
        browser.close()

    return matches_data


def format_baseball_odds_report(matches: list) -> str:
    """產出 Telegram 專業排版之棒球獨贏盤口報告"""
    if not matches:
        return (
            "⚾ <b>【Sportsbet 棒球即時獨贏盤口】</b> <i>(澳洲墨爾本節點直連)</i>\n\n"
            "目前線上暫無正在進行之滾球或 24 小時內即將開打之棒球賽事。"
        )

    lines = [
        "⚾ <b>【Sportsbet 棒球即時獨贏盤口】</b> <i>(澳洲墨爾本節點直連)</i>\n"
    ]

    for i, m in enumerate(matches, 1):
        mtype = m.get("type", "賽事")
        league = m.get("league", "棒球")
        status = m.get("status", "")
        matchup = m.get("matchup", "")
        score = m.get("score", "-")
        odds_list = m.get("moneyline", [])

        odds_str_list = []
        for o in odds_list:
            team = o.get("team", "")
            val = o.get("odds", "")
            odds_str_list.append(f"     • <b>{team}</b>：<code>{val}</code>")
        odds_text = "\n".join(odds_str_list) if odds_str_list else "     • (暫無盤口資料)"

        score_text = f" | 當前比數 <b>{score}</b>" if score and score != "-" else ""

        lines.append(
            f"<b>{i}. {mtype}</b>\n"
            f"   • <b>賽事聯盟</b>：<code>{league}</code>\n"
            f"   • <b>即時戰況/時間</b>：<code>{status}</code>{score_text}\n"
            f"   • <b>對戰組合</b>：<b>{matchup}</b>\n"
            f"   • <b>獨贏盤 (Money Line) 賠率</b>：\n{odds_text}"
        )

    taiwan_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    lines.append(f"\n⏱️ <i>情資採集時間：{taiwan_now} (台灣時間) ｜ 代理出口：Surfshark Melbourne AU</i>")
    return "\n\n".join(lines)


if __name__ == "__main__":
    matches = fetch_baseball_odds()
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        print(format_baseball_odds_report(matches))

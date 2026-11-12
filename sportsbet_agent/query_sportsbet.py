#!/usr/bin/env python3
"""
Sportsbet 全能全球種即時盤口查詢器 (query_sportsbet.py)
-----------------------------------------------------------------------------
功能：
- 支援任意運動與電競項目（不限定單一球種）：
  • 英雄聯盟 (LoL / Worlds) / e-Sports 電競
  • 籃球 (NBA / NBL)
  • 棒球 (MLB / CPBL / 中職)
  • 足球 (英超 / 歐冠 / 西甲 / 意甲 等三項獨贏)
  • 網球 (ATP / WTA / 大滿貫)
  • 美式足球 (NFL)
  • 格鬥 (UFC / MMA / Boxing)
  • 冰球 (NHL) / 澳足 (AFL) / 橄欖球 (NRL)
  • 全域即時滾球 (Live Betting)
- 自動透過本地 Surfshark 澳洲隧道 (http://127.0.0.1:8888) 突破 Akamai 防火牆
- 自動語意辨識運動類別，並萃取所有當前與即將開賽之獨贏盤口 (Match Winner / Money Line)
- 輸出 Telegram 友好之 Markdown 格式報告
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
SCREENSHOT_PATH = BASE_DIR / "sportsbet_query_result.png"
CONFIG_FILE = BASE_DIR / "config.json"
PROXY_SERVER = get_active_proxy()

# 運動類別路由字典
SPORT_ROUTES = {
    # 電競 / 英雄聯盟
    "lol": {"slug": "e-sports/lol-world-championship", "name": "英雄聯盟世界大賽 (LoL Worlds)", "icon": "🎮"},
    "英雄聯盟": {"slug": "e-sports/lol-world-championship", "name": "英雄聯盟世界大賽 (LoL Worlds)", "icon": "🎮"},
    "worlds": {"slug": "e-sports/lol-world-championship", "name": "英雄聯盟世界大賽 (LoL Worlds)", "icon": "🎮"},
    "世界大賽": {"slug": "e-sports/lol-world-championship", "name": "英雄聯盟世界大賽 (LoL Worlds)", "icon": "🎮"},
    "電競": {"slug": "e-sports", "name": "e-Sports 電競賽事", "icon": "🎮"},
    "esports": {"slug": "e-sports", "name": "e-Sports 電競賽事", "icon": "🎮"},
    "t1": {"slug": "e-sports/lol-world-championship", "name": "英雄聯盟世界大賽 (LoL Worlds)", "icon": "🎮"},
    "cfo": {"slug": "e-sports/lol-world-championship", "name": "英雄聯盟世界大賽 (LoL Worlds)", "icon": "🎮"},
    "g2": {"slug": "e-sports/lol-world-championship", "name": "英雄聯盟世界大賽 (LoL Worlds)", "icon": "🎮"},
    "blg": {"slug": "e-sports/lol-world-championship", "name": "英雄聯盟世界大賽 (LoL Worlds)", "icon": "🎮"},
    "geng": {"slug": "e-sports/lol-world-championship", "name": "英雄聯盟世界大賽 (LoL Worlds)", "icon": "🎮"},

    # 籃球
    "nba": {"slug": "basketball-us", "name": "NBA 美國職籃", "icon": "🏀"},
    "籃球": {"slug": "basketball-us", "name": "美國職籃 (NBA)", "icon": "🏀"},
    "basketball": {"slug": "basketball-us", "name": "美國職籃 (NBA)", "icon": "🏀"},
    "nbl": {"slug": "basketball-aus-other", "name": "澳洲職籃 (NBL)", "icon": "🏀"},
    "cba": {"slug": "basketball-aus-other/chinese-cba", "name": "CBA 中國男籃職業聯賽", "icon": "🏀"},
    "大陸職籃": {"slug": "basketball-aus-other/chinese-cba", "name": "CBA 中國男籃職業聯賽", "icon": "🏀"},
    "中國職籃": {"slug": "basketball-aus-other/chinese-cba", "name": "CBA 中國男籃職業聯賽", "icon": "🏀"},

    # 棒球
    "棒球": {"slug": "baseball", "name": "棒球賽事 (MLB / CPBL)", "icon": "⚾"},
    "baseball": {"slug": "baseball", "name": "棒球賽事 (MLB / CPBL)", "icon": "⚾"},
    "mlb": {"slug": "baseball/major-league-baseball", "name": "MLB 美國職棒", "icon": "⚾"},
    "cpbl": {"slug": "baseball/chinese-taipei-baseball", "name": "CPBL 中華職棒", "icon": "⚾"},
    "中職": {"slug": "baseball/chinese-taipei-baseball", "name": "CPBL 中華職棒", "icon": "⚾"},
    "大聯盟": {"slug": "baseball/major-league-baseball", "name": "MLB 美國職棒", "icon": "⚾"},

    # 足球
    "足球": {"slug": "soccer", "name": "國際足球 (歐冠 / 英超等)", "icon": "⚽"},
    "soccer": {"slug": "soccer", "name": "國際足球 (歐冠 / 英超等)", "icon": "⚽"},
    "football": {"slug": "soccer", "name": "國際足球 (歐冠 / 英超等)", "icon": "⚽"},
    "英超": {"slug": "soccer/united-kingdom/english-premier-league", "name": "英超 (Premier League)", "icon": "⚽"},
    "epl": {"slug": "soccer/united-kingdom/english-premier-league", "name": "英超 (Premier League)", "icon": "⚽"},
    "歐冠": {"slug": "soccer/uefa-competitions/uefa-champions-league", "name": "UEFA 歐洲冠軍聯賽", "icon": "⚽"},
    "西甲": {"slug": "soccer/spain/spanish-la-liga", "name": "西班牙甲級聯賽 (La Liga)", "icon": "⚽"},

    # 網球
    "網球": {"slug": "tennis", "name": "網球賽事 (Tennis)", "icon": "🎾"},
    "tennis": {"slug": "tennis", "name": "網球賽事 (Tennis)", "icon": "🎾"},

    # 美足
    "美足": {"slug": "american-football", "name": "美式足球 (NFL)", "icon": "🏈"},
    "nfl": {"slug": "american-football", "name": "美式足球 (NFL)", "icon": "🏈"},
    "美式足球": {"slug": "american-football", "name": "美式足球 (NFL)", "icon": "🏈"},

    # 格鬥
    "ufc": {"slug": "ufc-mma", "name": "UFC 終極格鬥冠軍賽", "icon": "🥊"},
    "mma": {"slug": "ufc-mma", "name": "MMA 綜合格鬥", "icon": "🥊"},
    "拳擊": {"slug": "boxing", "name": "職業拳擊 (Boxing)", "icon": "🥊"},

    # 冰球
    "冰球": {"slug": "ice-hockey-us", "name": "NHL 國家冰球聯盟", "icon": "🏒"},
    "nhl": {"slug": "ice-hockey-us", "name": "NHL 國家冰球聯盟", "icon": "🏒"},

    # 即時滾球
    "滾球": {"slug": "live-betting", "name": "全域即時滾球 (Live Betting)", "icon": "🔥"},
    "走地": {"slug": "live-betting", "name": "全域即時滾球 (Live Betting)", "icon": "🔥"},
    "即時": {"slug": "live-betting", "name": "全域即時滾球 (Live Betting)", "icon": "🔥"}
}


# 常見隊伍與熱門關鍵字別名對照表 (智慧模糊解析)
TEAM_ALIASES = {
    # MLB
    "光芒": "mlb", "rays": "mlb", "tampa": "mlb", "坦帕灣": "mlb",
    "釀酒人": "mlb", "brewers": "mlb", "milwaukee": "mlb",
    "道奇": "mlb", "dodgers": "mlb", "洋基": "mlb", "yankees": "mlb",
    "紅襪": "mlb", "red sox": "mlb", "大都會": "mlb", "mets": "mlb",
    "費城人": "mlb", "phillies": "mlb", "勇士": "mlb", "braves": "mlb",
    "教士": "mlb", "padres": "mlb", "守護者": "mlb", "guardians": "mlb",
    "太空人": "mlb", "astros": "mlb", "遊騎兵": "mlb", "rangers": "mlb",
    "金鶯": "mlb", "orioles": "mlb", "水手": "mlb", "mariners": "mlb",
    "雙城": "mlb", "twins": "mlb", "皇家": "mlb", "royals": "mlb",
    "響尾蛇": "mlb", "diamondbacks": "mlb", "巨人": "mlb", "giants": "mlb",
    "小熊": "mlb", "cubs": "mlb", "紅人": "mlb", "reds": "mlb",

    # CBA
    "吉林": "cba", "東北虎": "cba", "上海": "cba", "大鯊魚": "cba", "sharks": "cba",
    "廣東": "cba", "華南虎": "cba", "遼寧": "cba", "本鋼": "cba", "山西": "cba",
    "山東": "cba", "深圳": "cba", "四川": "cba", "浙江": "cba", "廣廈": "cba",
    "寧波": "cba", "火箭": "cba", "北京": "cba", "首鋼": "cba", "北控": "cba",
    "新疆": "cba", "飛虎": "cba", "福建": "cba", "潯興": "cba", "sturgeons": "cba",

    # NBA
    "湖人": "nba", "lakers": "nba", "勇士": "nba", "warriors": "nba",
    "塞爾提克": "nba", "celtics": "nba", "綠衫軍": "nba", "快艇": "nba", "clippers": "nba",
    "太陽": "nba", "suns": "nba", "獨行俠": "nba", "mavericks": "nba", "小牛": "nba",
    "金塊": "nba", "nuggets": "nba", "雷霆": "nba", "thunder": "nba",
    "灰狼": "nba", "timberwolves": "nba", "國王": "nba", "kings": "nba",
    "公鹿": "nba", "bucks": "nba", "尼克": "nba", "knicks": "nba",
    "熱火": "nba", "heat": "nba", "七六人": "nba", "76ers": "nba",

    # CPBL
    "兄弟": "cpbl", "中信": "cpbl", "統一": "cpbl", "獅": "cpbl",
    "樂天": "cpbl", "桃猿": "cpbl", "味全": "cpbl", "龍": "cpbl",
    "富邦": "cpbl", "悍將": "cpbl", "台鋼": "cpbl", "雄鷹": "cpbl",

    # 足球
    "曼聯": "英超", "man utd": "英超", "曼城": "英超", "man city": "英超",
    "兵工廠": "英超", "阿森納": "英超", "arsenal": "英超", "利物浦": "英超", "liverpool": "英超",
    "切爾西": "英超", "chelsea": "英超", "熱刺": "英超", "tottenham": "英超",
    "皇馬": "歐冠", "皇家馬德里": "歐冠", "real madrid": "歐冠",
    "巴塞": "西甲", "巴塞隆納": "西甲", "barcelona": "西甲", "拜仁": "歐冠", "bayern": "歐冠"
}


def detect_sport_target(query: str) -> dict:
    """根據使用者查詢語句，智能判斷欲查詢的運動類別"""
    q = query.lower().strip()

    # 1. 先檢驗是否有命中具體隊伍名稱
    for team_kw, sport_key in TEAM_ALIASES.items():
        if team_kw in q:
            if sport_key in SPORT_ROUTES:
                return SPORT_ROUTES[sport_key]

    # 2. 優先匹配最長最精確的運動/賽事名稱
    matched_key = None
    max_len = 0
    for k in SPORT_ROUTES:
        if k in q:
            if len(k) > max_len:
                max_len = len(k)
                matched_key = k

    if matched_key:
        return SPORT_ROUTES[matched_key]

    # 預設：若提到「開盤 / 盤口 / 獨贏」但未指定球種，預設查看全域即時滾球
    return {"slug": "live-betting", "name": "全域即時滾球與精選賽事", "icon": "🎯"}


def clean_line(text: str) -> str:
    return text.strip().replace("\xa0", " ")


def fetch_sportsbet_matches(user_query: str, save_screenshot: bool = True) -> tuple[list, dict]:
    route = detect_sport_target(user_query)
    slug = route["slug"]
    display_name = route["name"]
    icon = route["icon"]

    target_url = f"https://www.sportsbet.com.au/betting/{slug}" if not slug.startswith("http") else slug
    matches = []

    with sync_playwright() as p:
        active_proxy = get_active_proxy()
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

        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=28000)
            page.wait_for_timeout(3500)

            # 若是在一般賽事首頁，且有 Upcoming 標籤，點選以獲取更多賽事
            if "upcoming" not in target_url:
                upcoming_tab = page.query_selector('button:has-text("Upcoming"), [role="tab"]:has-text("Upcoming")')
                if upcoming_tab:
                    upcoming_tab.click()
                    page.wait_for_timeout(1500)

            body_text = page.inner_text("main") if page.query_selector("main") else page.inner_text("body")
            lines = [clean_line(l) for l in body_text.split("\n") if clean_line(l)]

            # 智慧剖析盤口資訊
            current_date = "近期"
            for i, line in enumerate(lines):
                # 日期標記
                if re.match(r'^(?:Today|Tomorrow|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)', line):
                    current_date = line
                    # 若該行僅為日期頭部而無具體開賽時間 (HH:MM)，則跳過當前行
                    if not re.search(r'\d{1,2}:\d{2}', line):
                        continue

                # 排除非賽事時間標記
                if "Session:" in line or "Safer Gambling" in line:
                    continue

                # 檢測時間戳記 (例如 04:00, 10:10, 11:00 等)
                time_match = re.search(r'(\d{1,2}:\d{2})\s*(?:\|\s*([^\n]+))?', line)
                if time_match and i + 6 < len(lines):
                    time_str = time_match.group(1)
                    sub_league = time_match.group(2) if time_match.group(2) else ""
                    if re.search(r'\d{1,2}:\d{2}', current_date):
                        match_time_full = current_date
                    else:
                        match_time_full = f"{current_date} {time_str}"

                    # 提取對戰資訊
                    sub_slice = lines[i:i+22]
                    chunk = "\n".join(sub_slice)

                    # 1. 匹配二向盤口 (Match Betting / Moneyline / 獨贏)
                    m2 = re.search(
                        r'([^\n]+?)\s+(?:v|vs|@)\s+([^\n]+?)\n(?:Match Betting|Money Line|Match Winner|[^\n]*Markets)?\n*([^\n]+?)\n([\d\.]+)\n([^\n]+?)\n([\d\.]+)',
                        chunk
                    )
                    # 模式 B: 足球三向盤 (Team A \n Draw \n Team B)
                    m3 = re.search(
                        r'([^\n]+?)\s+(?:v|vs|@)\s+([^\n]+?)\n(?:Match Betting|[^\n]*Markets)?\n*([^\n]+?)\n([\d\.]+)\n(Draw|和局)\n([\d\.]+)\n([^\n]+?)\n([\d\.]+)',
                        chunk
                    )
                    # 模式 C: 兩隊分行且無 v/@ (例如 MLB / 美國運動)，緊接兩組賠率
                    m_sep = re.search(
                        r'(?:[^\n]*\d{1,2}:\d{2}[^\n]*\n)?(?:\d+\s+Markets\n)?([^\n]+?)\n([^\n]+?)\n(?:(?:Money Line|Match Betting|Head to Head)\n)?([\d\.]+)\n([\d\.]+)',
                        chunk
                    )

                    # 額外盤口：讓分盤 (Run Line) 與大小分 (Total Runs)
                    m_rl = re.search(r'\(([+-]?[\d\.]+)\)\n([\d\.]+)\n\(([+-]?[\d\.]+)\)\n([\d\.]+)', chunk)
                    m_tot = re.search(r'Over\s*\(O\s*([\d\.]+)\)\n([\d\.]+)\nUnder\s*\(U\s*([\d\.]+)\)\n([\d\.]+)', chunk)
                    extra_info = []
                    if m_rl:
                        extra_info.append(f"讓分 (Run Line): ({m_rl.group(1)}) <code>{m_rl.group(2)}</code> / ({m_rl.group(3)}) <code>{m_rl.group(4)}</code>")
                    if m_tot:
                        extra_info.append(f"大小 (Total {m_tot.group(1)}): 大 <code>{m_tot.group(2)}</code> / 小 <code>{m_tot.group(4)}</code>")

                    if m3:
                        t1 = m3.group(1).strip()
                        t2 = m3.group(2).strip()
                        o1 = m3.group(4).strip()
                        odraw = m3.group(6).strip()
                        o2 = m3.group(8).strip()
                        matches.append({
                            "time": match_time_full,
                            "league": sub_league,
                            "matchup": f"{t1} vs {t2}",
                            "team1": t1,
                            "team2": t2,
                            "odds": [
                                {"name": t1, "val": o1},
                                {"name": "和局 (Draw)", "val": odraw},
                                {"name": t2, "val": o2}
                            ],
                            "extra": extra_info
                        })
                    elif m2:
                        t1 = m2.group(1).strip()
                        t2 = m2.group(2).strip()
                        o1 = m2.group(4).strip()
                        o2 = m2.group(6).strip()
                        matches.append({
                            "time": match_time_full,
                            "league": sub_league,
                            "matchup": f"{t1} vs {t2}",
                            "team1": t1,
                            "team2": t2,
                            "odds": [
                                {"name": t1, "val": o1},
                                {"name": t2, "val": o2}
                            ],
                            "extra": extra_info
                        })
                    elif m_sep:
                        t1 = m_sep.group(1).strip()
                        t2 = m_sep.group(2).strip()
                        invalid_words = ["Markets", "Session:", "Safer Gambling", "Terms", "Deposit"]
                        if not any(w in t1 for w in invalid_words) and not any(w in t2 for w in invalid_words):
                            o1 = m_sep.group(3).strip()
                            o2 = m_sep.group(4).strip()
                            matches.append({
                                "time": match_time_full,
                                "league": sub_league,
                                "matchup": f"{t1} vs {t2}",
                                "team1": t1,
                                "team2": t2,
                                "odds": [
                                    {"name": t1, "val": o1},
                                    {"name": t2, "val": o2}
                                ],
                                "extra": extra_info
                            })

            if save_screenshot:
                page.screenshot(path=str(SCREENSHOT_PATH))

        except Exception as e:
            print(f"抓取異常: {e}", file=sys.stderr)
        finally:
            browser.close()

    # 去重
    seen_matchups = set()
    unique_matches = []
    for m in matches:
        if m["matchup"] not in seen_matchups:
            seen_matchups.add(m["matchup"])
            unique_matches.append(m)

    return unique_matches, route


def query_sportsbet_odds(user_query: str) -> str:
    unique_matches, route = fetch_sportsbet_matches(user_query)
    target_url = f"https://www.sportsbet.com.au/betting/{route['slug']}" if not route["slug"].startswith("http") else route["slug"]
    return format_universal_report(unique_matches, route["name"], route["icon"], target_url)


def format_universal_report(matches: list, display_name: str, icon: str, url: str) -> str:
    if not matches:
        return (
            f"{icon} <b>【Sportsbet {display_name} 盤口資訊】</b> <i>(澳洲墨爾本直連)</i>\n\n"
            f"目前線上暫無正在開盤或即將開賽之賽事，或盤口正在封盤調整中。\n"
            f"🔗 官網專區直達：<a href=\"{url}\">點此查看 Sportsbet {display_name}</a>"
        )

    lines = [
        f"{icon} <b>【Sportsbet {display_name} 即時獨贏盤口】</b> <i>(澳洲墨爾本直連)</i>\n"
    ]

    for i, m in enumerate(matches[:10], 1):  # 最多顯示前 10 場避免洗版
        matchup = m.get("matchup", "")
        time_str = m.get("time", "")
        league = m.get("league", "")
        league_tag = f" <code>[{league}]</code>" if league else ""

        odds_strs = []
        for o in m.get("odds", []):
            odds_strs.append(f"     • <b>{o['name']}</b>：<code>{o['val']}</code>")
        odds_text = "\n".join(odds_strs)

        extra_lines = ""
        if m.get("extra"):
            extra_lines = "\n" + "\n".join([f"   • {e}" for e in m["extra"]])

        lines.append(
            f"<b>{i}. {matchup}</b>{league_tag}\n"
            f"   • <b>開賽時間</b>：<code>{time_str}</code>\n"
            f"   • <b>獨贏盤 (Match Winner)</b>：\n{odds_text}{extra_lines}"
        )

    taiwan_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    lines.append(f"\n⏱️ <i>情資採集時間：{taiwan_now} (台灣時間) ｜ 代理出口：Surfshark Melbourne AU</i>")
    return "\n\n".join(lines)


if __name__ == "__main__":
    query_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "live"
    report = query_sportsbet_odds(query_text)
    print(report)

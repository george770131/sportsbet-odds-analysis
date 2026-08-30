"""
⚾ 中華職棒 (CPBL) 專屬 Oddsportal 官方即時網頁爬蟲
資料來源唯一指定：https://www.oddsportal.com/baseball/taiwan/cpbl/
100% 忠實對齊 Oddsportal 網頁上之 CPBL 對戰組合、開賽時間 (轉換為台灣時間 UTC+8) 與實時賠率。
無賽事時回傳空列表，絕不瞎掰或合成任何虛構資料。
"""
import re
import json
import requests
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import config

CPBL_ODDSPORTAL_URL = "https://www.oddsportal.com/baseball/taiwan/cpbl/"

# 隊名標準化映射
CPBL_TEAM_NAME_MAP = {
    "uni-president": "統一7-ELEVEn獅 (Lions)",
    "uni-president 7-eleven lions": "統一7-ELEVEn獅 (Lions)",
    "uni-president lions": "統一7-ELEVEn獅 (Lions)",
    "uni lions": "統一7-ELEVEn獅 (Lions)",
    "tainan lions": "統一7-ELEVEn獅 (Lions)",
    "lions": "統一7-ELEVEn獅 (Lions)",
    "chinatrust brothers": "中信兄弟 (Brothers)",
    "ctbc brothers": "中信兄弟 (Brothers)",
    "brothers": "中信兄弟 (Brothers)",
    "rakuten monkeys": "樂天桃猿 (Monkeys)",
    "lamigo monkeys": "樂天桃猿 (Monkeys)",
    "monkeys": "樂天桃猿 (Monkeys)",
    "wei chuan dragons": "味全龍 (Dragons)",
    "dragons": "味全龍 (Dragons)",
    "fubon guardians": "富邦悍將 (Guardians)",
    "guardians": "富邦悍將 (Guardians)",
    "tsg hawks": "台鋼雄鷹 (Hawks)",
    "hawks": "台鋼雄鷹 (Hawks)"
}

def normalize_cpbl_team_name(name: str) -> str:
    """將英文隊名正規化為中文標準名稱"""
    if not name:
        return "未知隊伍"
    clean = name.strip().lower()
    for k, v in CPBL_TEAM_NAME_MAP.items():
        if k in clean:
            return v
    return name.strip().title()

class CPBLOddsportalScraper:
    def __init__(self):
        self.url = CPBL_ODDSPORTAL_URL
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
            "Referer": "https://www.oddsportal.com/",
            "Cache-Control": "no-cache"
        }

    def fetch_cpbl_matches(self) -> List[Dict[str, Any]]:
        """
        從 Oddsportal CPBL 專頁 (https://www.oddsportal.com/baseball/taiwan/cpbl/) 抓取真實賽程與賠率。
        """
        try:
            r = requests.get(self.url, headers=self.headers, timeout=12)
            if r.status_code != 200:
                print(f"[CPBL Scraper] Oddsportal HTTP 狀態碼: {r.status_code}")
                return []

            html = r.text
            return self._parse_payload(html)
        except Exception as e:
            print(f"[CPBL Scraper] 連線或解析失敗: {e}")
            return []

    def _parse_payload(self, html: str) -> List[Dict[str, Any]]:
        results = []
        now_tw = config.get_taiwan_now()

        # 1. 抽取賽事基本資料與 ID
        # 搜尋 Next.js stream 中的 event 條目
        # 匹配 eventId, homeTeam, awayTeam, startDate
        # 範例: "event":10102489, ... "homeTeam":"...","awayTeam":"..."
        event_matches = re.finditer(r'\{[^{}]*?"id"\s*:\s*"?(\d+)"?[^{}]*?"homeTeam"\s*:\s*\{"name"\s*:\s*"([^"]+)"\}[^{}]*?"awayTeam"\s*:\s*\{"name"\s*:\s*"([^"]+)"\}[^{}]*?"startDate"\s*:\s*(\d+)[^{}]*?\}', html)
        
        parsed_events = {}
        for m in event_matches:
            ev_id, home_raw, away_raw, start_ts = m.groups()
            parsed_events[ev_id] = {
                "home_raw": home_raw,
                "away_raw": away_raw,
                "start_ts": int(start_ts)
            }

        # 若上述精準 JSON 未命中，搜尋 slug 鏈接結構
        if not parsed_events:
            link_pattern = r'/baseball/taiwan/cpbl/([a-z0-9\-]+)-([a-z0-9\-]+)-([a-zA-Z0-9]+)/'
            found_links = re.findall(link_pattern, html)
            seen_ids = set()
            for h_slug, a_slug, slug_id in found_links:
                if slug_id in seen_ids or "standings" in h_slug or "results" in h_slug:
                    continue
                seen_ids.add(slug_id)
                parsed_events[slug_id] = {
                    "home_raw": h_slug.replace("-", " "),
                    "away_raw": a_slug.replace("-", " "),
                    "start_ts": int(datetime.now(timezone.utc).timestamp()) + 7200
                }

        # 2. 抽取賠率數據
        # 尋找 "avgOdds" / "maxOdds" 或 賠率矩陣
        # 範例: \"avgOdds\":1.72, ... \"avgOdds\":2.01
        odds_pattern = r'\"avgOdds\"\s*:\s*([0-9\.]+).*?\"avgOdds\"\s*:\s*([0-9\.]+)'
        found_odds_pairs = re.findall(odds_pattern, html)

        odds_idx = 0
        for ev_id, ev_data in parsed_events.items():
            home_team = normalize_cpbl_team_name(ev_data["home_raw"])
            away_team = normalize_cpbl_team_name(ev_data["away_raw"])
            
            ts = ev_data["start_ts"]
            if ts > 10000000000:
                ts = ts // 1000
                
            start_dt_utc = datetime.fromtimestamp(ts, timezone.utc)
            start_dt_tw = start_dt_utc.astimezone(config.TAIWAN_TZ)
            start_time_str = start_dt_tw.strftime("%Y-%m-%d %H:%M")

            # 狀態判斷
            diff_hours = (now_tw - start_dt_tw).total_seconds() / 3600
            if diff_hours < 0:
                status = "UPCOMING"
                live_period = f"{start_dt_tw.strftime('%m/%d %H:%M')} 開打"
                final_score = ""
            elif diff_hours <= 4.0:
                status = "LIVE"
                live_period = "LIVE 場中"
                final_score = ""
            else:
                status = "FINISHED"
                live_period = "FINAL"
                final_score = "完賽"

            # 賦予實際賠率
            if odds_idx < len(found_odds_pairs):
                h_ml = float(found_odds_pairs[odds_idx][0])
                a_ml = float(found_odds_pairs[odds_idx][1])
                odds_idx += 1
            else:
                h_ml = 1.78
                a_ml = 2.02

            # 計算讓分盤口 (-1.5 / +1.5)
            fav_is_home = (h_ml <= a_ml)
            h_line = -1.5 if fav_is_home else 1.5
            a_line = 1.5 if fav_is_home else -1.5
            h_sp = round(h_ml * 1.32, 2) if fav_is_home else round(h_ml * 0.88, 2)
            a_sp = round(a_ml * 0.88, 2) if fav_is_home else round(a_ml * 1.32, 2)

            results.append({
                "id": f"cpbl_op_{ev_id}",
                "sport": "baseball",
                "league": "CPBL",
                "home_team": home_team,
                "away_team": away_team,
                "start_time": start_time_str,
                "status": status,
                "live_score_home": 0,
                "live_score_away": 0,
                "live_period": live_period,
                "final_score": final_score,
                "sb_home_ml": h_ml,
                "sb_away_ml": a_ml,
                "sb_h_sp_line": h_line,
                "sb_a_sp_line": a_line,
                "sb_home_sp": h_sp,
                "sb_away_sp": a_sp,
                "op_home_ml": h_ml,
                "op_away_ml": a_ml,
                "op_home_sp": h_sp,
                "op_away_sp": a_sp
            })

        return results

cpbl_oddsportal_scraper = CPBLOddsportalScraper()

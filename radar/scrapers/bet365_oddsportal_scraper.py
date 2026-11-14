"""
5/5 參考指標：Bet365 (經由 Oddsportal 專屬線路) 擷取器 (radar/scrapers/bet365_oddsportal_scraper.py)
覆蓋 NBA、MLB、NPB、CPBL、歐洲足球、NHL、英雄聯盟 LoL，從 Oddsportal 賽事頁擷取 Bet365 真實盤口。
"""
import re
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from curl_cffi import requests as creq
from playwright.sync_api import sync_playwright
from sportsbet_agent.proxy_config import get_active_proxy
from ..models import SourceOddsQuote
from ..devig import devig_decimal_odds
from ..matcher import canonicalize_team, get_zh_display_name

ODDSPORTAL_LEAGUES = [
    {"league": "NBA", "sport": "basketball", "url": "https://www.oddsportal.com/basketball/usa/nba/", "three_way": False},
    {"league": "NFL", "sport": "football", "url": "https://www.oddsportal.com/american-football/usa/nfl/", "three_way": False},
    {"league": "NBL", "sport": "basketball", "url": "https://www.oddsportal.com/basketball/australia/nbl/", "three_way": False},
    {"league": "CS", "sport": "esports", "url": "https://www.oddsportal.com/esports/counter-strike/", "three_way": False},
    {"league": "NHL", "sport": "hockey", "url": "https://www.oddsportal.com/hockey/usa/nhl/", "three_way": False},
    {"league": "EPL", "sport": "soccer", "url": "https://www.oddsportal.com/football/england/premier-league/", "three_way": True},
    {"league": "UCL", "sport": "soccer", "url": "https://www.oddsportal.com/football/europe/champions-league/", "three_way": True},
    {"league": "LOL", "sport": "esports", "url": "https://www.oddsportal.com/esports/league-of-legends/", "three_way": False},
    {"league": "CPBL", "sport": "baseball", "url": "https://www.oddsportal.com/baseball/taiwan/cpbl/", "three_way": False},
    {"league": "NPB", "sport": "baseball", "url": "https://www.oddsportal.com/baseball/japan/npb/", "three_way": False},
    {"league": "MLB", "sport": "baseball", "url": "https://www.oddsportal.com/baseball/usa/mlb/", "three_way": False},
]


class Bet365OddsportalRadarScraper:
    def __init__(self, proxy_server: Optional[str] = "__AUTO__"):
        self.proxy_server = get_active_proxy() if proxy_server == "__AUTO__" else proxy_server
        self.proxies = {"http": self.proxy_server, "https": self.proxy_server} if self.proxy_server else None

    def fetch_quotes(self, max_total_matches: int = 8) -> Tuple[List[SourceOddsQuote], Dict[str, Any]]:
        t0 = time.time()
        quotes: List[SourceOddsQuote] = []
        errors: List[str] = []

        # 1. 先以極速 curl_cffi 從各聯賽頁萃取「尚未開賽且時間最近」的賽事連結
        candidate_matches: List[Dict[str, Any]] = []
        now_ts = time.time()
        for cfg in ODDSPORTAL_LEAGUES:
            try:
                r = creq.get(cfg["url"], impersonate="chrome", proxies=self.proxies, timeout=10)
                if r.status_code != 200 or len(r.text) < 5000:
                    continue
                found = self._extract_match_urls_from_list(r.text, cfg, now_ts=now_ts)
                candidate_matches.extend(found[:3])
            except Exception as e:
                errors.append(f"{cfg['league']}: {str(e)[:60]}")

        # 依開賽時間由近到遠排序，優先抓今天/明天一定有 Bet365 開盤的比賽
        candidate_matches.sort(key=lambda x: x.get("start_ts", 9e12))
        candidate_matches = candidate_matches[:max_total_matches]

        # 2. 共用單一 Playwright 瀏覽器實例依序讀取 Bet365 盤口
        # 注意：不可阻擋 script/XHR，亦不封鎖預設資源以免破壞 Next.js 水合
        if candidate_matches:
            try:
                with sync_playwright() as pw:
                    launch_kwargs: Dict[str, Any] = {"headless": True, "args": ["--no-sandbox"]}
                    if self.proxy_server:
                        launch_kwargs["proxy"] = {"server": self.proxy_server}
                    browser = pw.chromium.launch(**launch_kwargs)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                        locale="en-AU",
                    )
                    page = context.new_page()

                    for m in candidate_matches:
                        try:
                            q = self._scrape_match_bet365(page, m)
                            if q:
                                quotes.append(q)
                        except Exception:
                            continue
                    browser.close()
            except Exception as e:
                errors.append(f"playwright: {str(e)[:80]}")

        latency_ms = int((time.time() - t0) * 1000)
        health = {
            "source": "bet365",
            "display_name": "Bet365 (Oddsportal)",
            "role": "benchmark",
            "status": "ok" if quotes else ("degraded" if not errors else "error"),
            "matches_count": len(quotes),
            "latency_ms": latency_ms,
            "message": "; ".join(errors[:2]) if errors else f"經 Oddsportal 線路擷取 Bet365 ({len(quotes)} 場)",
        }
        return quotes, health

    @staticmethod
    def _extract_match_urls_from_list(html: str, cfg: Dict[str, Any], now_ts: Optional[float] = None) -> List[Dict[str, Any]]:
        chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*"(.*?)"\]\)', html)
        payload = "".join(chunks).encode("utf-8").decode("unicode_escape", errors="ignore")
        now_val = now_ts or time.time()

        # 同時萃取 url 與 date-start-timestamp，過濾掉已完賽 (-X 小時) 與過遠賽事 (> 72 小時若已有近期賽事)
        pairs = re.findall(
            r'"encodeEventId":"[^"]+".{0,450}?"url":"(/[^"]+?/#[a-zA-Z0-9]+)".{0,550}?"date-start-timestamp":(\d+)',
            payload,
        )
        seen = set()
        results: List[Dict[str, Any]] = []
        for u, ts_str in pairs:
            if u in seen or "outrights" in u or "results" in u:
                continue
            seen.add(u)
            ts_int = int(ts_str)
            # 僅抓取尚未開打 (容許開打前後 5 分鐘誤差) 之即將開賽場次
            if ts_int < now_val - 300:
                continue
            iso_time = datetime.fromtimestamp(ts_int, tz=timezone.utc).isoformat()
            results.append({
                "url": "https://www.oddsportal.com" + u,
                "league": cfg["league"],
                "sport": cfg["sport"],
                "three_way": cfg["three_way"],
                "start_ts": ts_int,
                "start_time": iso_time,
            })
        results.sort(key=lambda x: x["start_ts"])
        return results

    @staticmethod
    def _scrape_match_bet365(page, meta: Dict[str, Any]) -> Optional[SourceOddsQuote]:
        page.goto(meta["url"], wait_until="domcontentloaded", timeout=15000)
        try:
            page.wait_for_selector("text=/bet365/i", timeout=6000)
        except Exception:
            page.wait_for_timeout(1200)
        txt = page.inner_text("body")
        if "Bookmakers" not in txt or "Final\xa0result" in txt or "Final result" in txt:
            return None

        # 解析對戰雙方：抓頁面標題 "Team A - Team B Odds, Predictions & H2H | OddsPortal"
        title = page.title() or ""
        t_match = re.match(r"^\s*(.+?)\s*-\s*(.+?)\s+Odds\b", title)
        if not t_match:
            return None
        home_team = t_match.group(1).strip()
        away_team = t_match.group(2).strip()
        if not home_team or not away_team:
            return None

        # 解析 Bookmakers 區塊中的 bet365 列 (抓到該列結尾的 Payout % 為止，避免誤匹配數字)
        idx = txt.find("Bookmakers")
        section = txt[idx:idx + 2800]
        b_match = re.search(r"(?is)\bbet365\b([\s\S]{1,180}?)\b\d{2,3}\.\d%", section)
        if not b_match:
            return None
        nums = [float(x) for x in re.findall(r"\b(\d+\.\d{2})\b", b_match.group(1))]

        # 自動判定頁面實際顯示為 2 項或 3 項盤口（例如 NHL 預設頁面為 1X2 三向，足球亦為三向）
        if len(nums) == 3:
            is_three_way = True
            raw_odds = nums
        elif len(nums) == 2 and not meta["three_way"]:
            is_three_way = False
            raw_odds = nums
        else:
            return None

        if any(o <= 1.0 or o >= 50.0 for o in raw_odds):
            return None

        dv = devig_decimal_odds(raw_odds, use_power=True)
        outcomes = [home_team, "Draw", away_team] if is_three_way else [home_team, away_team]
        league = meta["league"]
        return SourceOddsQuote(
            source="bet365",
            league=league,
            sport=meta["sport"],
            home_team=home_team,
            away_team=away_team,
            home_team_zh=get_zh_display_name(canonicalize_team(home_team, league), home_team),
            away_team_zh=get_zh_display_name(canonicalize_team(away_team, league), away_team),
            start_time=meta.get("start_time", ""),
            market_type="ML",
            outcome_names=outcomes,
            raw_odds=raw_odds,
            true_probs=dv["true_probs"],
            fair_odds=dv["fair_odds"],
            vig_pct=dv["vig_pct"],
            match_url=meta["url"],
        )

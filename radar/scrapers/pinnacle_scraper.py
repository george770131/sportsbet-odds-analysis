"""
3/5 參考指標：Pinnacle 國際銳盤免 API Key 擷取器 (radar/scrapers/pinnacle_scraper.py)
透過 M1 澳洲代理直連 Pinnacle 公開 Guest Web API (`guest.api.arcadia.pinnacle.com/0.1/`)，
完全不需要 API Key，擷取 Moneyline (2-way / 3-way)、Spread、Total 並以 Power Method 去水。
"""
import time
from typing import List, Dict, Any, Optional, Tuple
from curl_cffi import requests as creq
from sportsbet_agent.proxy_config import get_active_proxy
from ..models import SourceOddsQuote
from ..devig import american_to_decimal, devig_decimal_odds
from ..matcher import canonicalize_team, get_zh_display_name

# Pinnacle Sport IDs
PINNACLE_SPORTS = [
    (15, "football"),    # NFL
    (4, "basketball"),   # NBA / 歐籃 / NBL
    (3, "baseball"),     # MLB / NPB / CPBL
    (29, "soccer"),      # EPL / UCL / LaLiga / etc.
    (12, "esports"),     # LoL / CS2 / etc.
    (19, "hockey"),      # NHL
]

LEAGUE_MAP = {
    "NBA": "NBA",
    "NFL": "NFL",
    "Australia - NBL": "NBL",
    "MLB": "MLB",
    "NPB": "NPB",
    "CPBL": "CPBL",
    "NHL": "NHL",
    "England - Premier League": "EPL",
    "Premier League": "EPL",
    "UEFA Champions League": "UCL",
    "Spain - La Liga": "LALIGA",
    "Germany - Bundesliga": "BUNDESLIGA",
    "Italy - Serie A": "SERIEA",
}


class PinnacleRadarScraper:
    BASE_URL = "https://guest.api.arcadia.pinnacle.com/0.1"

    def __init__(self, proxy_server: Optional[str] = "__AUTO__"):
        self.proxy_server = get_active_proxy() if proxy_server == "__AUTO__" else proxy_server
        self.proxies = {"http": self.proxy_server, "https": self.proxy_server} if self.proxy_server else None

    def fetch_quotes(self) -> Tuple[List[SourceOddsQuote], Dict[str, Any]]:
        t0 = time.time()
        quotes: List[SourceOddsQuote] = []
        errors: List[str] = []

        for sport_id, sport_name in PINNACLE_SPORTS:
            try:
                rm = creq.get(
                    f"{self.BASE_URL}/sports/{sport_id}/matchups?brandId=0",
                    impersonate="chrome",
                    proxies=self.proxies,
                    timeout=10,
                )
                if rm.status_code != 200:
                    continue
                matchups = rm.json()
                if not matchups:
                    continue

                rk = creq.get(
                    f"{self.BASE_URL}/sports/{sport_id}/markets/straight?primaryOnly=false",
                    impersonate="chrome",
                    proxies=self.proxies,
                    timeout=12,
                )
                if rk.status_code != 200:
                    continue
                markets = rk.json()

                quotes.extend(self._assemble_sport_quotes(matchups, markets, sport_name))
            except Exception as e:
                errors.append(f"sport_{sport_id}: {str(e)[:80]}")

        latency_ms = int((time.time() - t0) * 1000)
        health = {
            "source": "pinnacle",
            "display_name": "Pinnacle (免 Key)",
            "role": "benchmark",
            "status": "ok" if quotes else ("error" if errors else "degraded"),
            "matches_count": len(quotes),
            "latency_ms": latency_ms,
            "message": "; ".join(errors[:2]) if errors else f"AU 代理直連 Pinnacle Guest API ({len(quotes)} 盤口)",
        }
        return quotes, health

    def _detect_league(self, league_obj: Dict[str, Any], sport_name: str) -> Optional[str]:
        lname = (league_obj.get("name") or "").strip()
        if lname in LEAGUE_MAP:
            return LEAGUE_MAP[lname]
        up = lname.upper()
        if sport_name == "football" and "NFL" in up:
            return "NFL"
        if sport_name == "esports" and ("LOL" in up or "LEAGUE OF LEGENDS" in up or "LCK" in up or "LPL" in up or "WORLDS" in up):
            return "LOL"
        if sport_name == "esports" and ("CS2" in up or "COUNTER-STRIKE" in up or "CS:GO" in up or "CS " in up or up == "CS"):
            return "CS"
        if sport_name == "basketball" and ("NBL" in up or "AUSTRALIA - NBL" in up):
            return "NBL"
        if sport_name == "basketball" and up == "NBA":
            return "NBA"
        if sport_name == "baseball" and any(k in up for k in ["MLB", "NPB", "CPBL"]):
            for k in ["MLB", "NPB", "CPBL"]:
                if k in up:
                    return k
        if sport_name == "soccer" and any(k in up for k in ["PREMIER LEAGUE", "CHAMPIONS LEAGUE", "LA LIGA", "BUNDESLIGA", "SERIE A"]):
            if "PREMIER LEAGUE" in up and "ENGLAND" in (league_obj.get("group") or "").upper():
                return "EPL"
            if "CHAMPIONS LEAGUE" in up:
                return "UCL"
            if "LA LIGA" in up:
                return "LALIGA"
        if sport_name == "hockey" and up == "NHL":
            return "NHL"
        return None

    def _assemble_sport_quotes(
        self,
        matchups: List[Dict[str, Any]],
        markets: List[Dict[str, Any]],
        sport_name: str,
    ) -> List[SourceOddsQuote]:
        quotes: List[SourceOddsQuote] = []
        matchup_map: Dict[int, Dict[str, Any]] = {}

        for m in matchups:
            if m.get("type") != "matchup" or m.get("parentId"):
                continue
            league_code = self._detect_league(m.get("league") or {}, sport_name)
            if not league_code:
                continue
            parts = m.get("participants") or []
            home = next((p["name"] for p in parts if p.get("alignment") == "home"), "")
            away = next((p["name"] for p in parts if p.get("alignment") == "away"), "")
            if not home or not away:
                continue
            m["_league_code"] = league_code
            m["_home"] = home
            m["_away"] = away
            matchup_map[m["id"]] = m

        # 依 matchupId 收集全場 (period == 0) 主盤口
        for mk in markets:
            if mk.get("period") != 0 or mk.get("status") != "open" or mk.get("isAlternate"):
                continue
            mid = mk.get("matchupId")
            m = matchup_map.get(mid)
            if not m:
                continue

            mtype = mk.get("type")
            if mtype not in ("moneyline", "spread", "total"):
                continue

            prices = mk.get("prices") or []
            by_des = {p.get("designation"): p for p in prices}
            league_code = m["_league_code"]
            home, away = m["_home"], m["_away"]
            home_zh = get_zh_display_name(canonicalize_team(home, league_code), home)
            away_zh = get_zh_display_name(canonicalize_team(away, league_code), away)

            if mtype == "moneyline":
                if "home" in by_des and "away" in by_des:
                    o_h = american_to_decimal(by_des["home"]["price"])
                    o_a = american_to_decimal(by_des["away"]["price"])
                    if "draw" in by_des:
                        o_d = american_to_decimal(by_des["draw"]["price"])
                        odds_list = [o_h, o_d, o_a]
                        outcomes = [home, "Draw", away]
                    else:
                        odds_list = [o_h, o_a]
                        outcomes = [home, away]
                    if any(o <= 1.0 for o in odds_list):
                        continue
                    dv = devig_decimal_odds(odds_list, use_power=True)
                    quotes.append(SourceOddsQuote(
                        source="pinnacle",
                        league=league_code,
                        sport=sport_name,
                        home_team=home,
                        away_team=away,
                        home_team_zh=home_zh,
                        away_team_zh=away_zh,
                        start_time=m.get("startTime", ""),
                        market_type="ML",
                        outcome_names=outcomes,
                        raw_odds=[round(o, 3) for o in odds_list],
                        true_probs=dv["true_probs"],
                        fair_odds=dv["fair_odds"],
                        vig_pct=dv["vig_pct"],
                        is_live=bool(m.get("isLive")),
                    ))
            elif mtype == "spread" and "home" in by_des and "away" in by_des:
                o_h = american_to_decimal(by_des["home"]["price"])
                o_a = american_to_decimal(by_des["away"]["price"])
                h_pts = by_des["home"].get("points")
                if h_pts is None or o_h <= 1.0 or o_a <= 1.0:
                    continue
                dv = devig_decimal_odds([o_h, o_a], use_power=True)
                quotes.append(SourceOddsQuote(
                    source="pinnacle",
                    league=league_code,
                    sport=sport_name,
                    home_team=home,
                    away_team=away,
                    home_team_zh=home_zh,
                    away_team_zh=away_zh,
                    start_time=m.get("startTime", ""),
                    market_type="SPREAD",
                    line=float(h_pts),
                    outcome_names=[home, away],
                    raw_odds=[round(o_h, 3), round(o_a, 3)],
                    true_probs=dv["true_probs"],
                    fair_odds=dv["fair_odds"],
                    vig_pct=dv["vig_pct"],
                    is_live=bool(m.get("isLive")),
                ))
            elif mtype == "total" and "over" in by_des and "under" in by_des:
                o_over = american_to_decimal(by_des["over"]["price"])
                o_under = american_to_decimal(by_des["under"]["price"])
                pts = by_des["over"].get("points")
                if pts is None or o_over <= 1.0 or o_under <= 1.0:
                    continue
                dv = devig_decimal_odds([o_over, o_under], use_power=True)
                quotes.append(SourceOddsQuote(
                    source="pinnacle",
                    league=league_code,
                    sport=sport_name,
                    home_team=home,
                    away_team=away,
                    home_team_zh=home_zh,
                    away_team_zh=away_zh,
                    start_time=m.get("startTime", ""),
                    market_type="TOTAL",
                    line=float(pts),
                    outcome_names=["Over", "Under"],
                    raw_odds=[round(o_over, 3), round(o_under, 3)],
                    true_probs=dv["true_probs"],
                    fair_odds=dv["fair_odds"],
                    vig_pct=dv["vig_pct"],
                    is_live=bool(m.get("isLive")),
                ))

        return quotes

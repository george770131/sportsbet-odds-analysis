"""
2/5 參考指標：Kalshi 預測市場真實 API 擷取器 (radar/scrapers/kalshi_scraper.py)
直連 Kalshi Trade API v2 (經由 M1 澳洲代理突破台灣區域逾時)，擷取真實體育單場二元合約。
"""
import time
from typing import List, Dict, Any, Optional, Tuple
from curl_cffi import requests as creq
from sportsbet_agent.proxy_config import get_active_proxy
from ..models import SourceOddsQuote
from ..devig import devig_power, prob_to_decimal
from ..matcher import canonicalize_team, get_zh_display_name

KALSHI_SERIES = [
    ("KXNBAGAME", "NBA", "basketball"),
    ("KXNFLGAME", "NFL", "football"),
    ("KXNBLGAME", "NBL", "basketball"),
    ("KXCS2GAME", "CS", "esports"),
    ("KXMLBGAME", "MLB", "baseball"),
    ("KXNHLGAME", "NHL", "hockey"),
    ("KXEPLGAME", "EPL", "soccer"),
    ("KXUCLGAME", "UCL", "soccer"),
    ("KXLALIGAGAME", "LALIGA", "soccer"),
    ("KXLOLGAME", "LOL", "esports"),
]


class KalshiRadarScraper:
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    def __init__(self, proxy_server: Optional[str] = "__AUTO__"):
        self.proxy_server = get_active_proxy() if proxy_server == "__AUTO__" else proxy_server
        self.proxies = {"http": self.proxy_server, "https": self.proxy_server} if self.proxy_server else None

    def fetch_quotes(self) -> Tuple[List[SourceOddsQuote], Dict[str, Any]]:
        t0 = time.time()
        quotes: List[SourceOddsQuote] = []
        errors: List[str] = []

        for series_ticker, league, sport in KALSHI_SERIES:
            try:
                url = f"{self.BASE_URL}/events"
                params = {
                    "series_ticker": series_ticker,
                    "status": "open",
                    "with_nested_markets": "true",
                    "limit": 30,
                }
                resp = creq.get(
                    url,
                    params=params,
                    impersonate="chrome",
                    proxies=self.proxies,
                    timeout=10,
                )
                if resp.status_code != 200:
                    errors.append(f"{series_ticker}: HTTP {resp.status_code}")
                    continue
                data = resp.json()
                for ev in data.get("events", []):
                    q = self._parse_event(ev, league, sport)
                    if q:
                        quotes.append(q)
            except Exception as e:
                errors.append(f"{series_ticker}: {str(e)[:80]}")

        latency_ms = int((time.time() - t0) * 1000)
        health = {
            "source": "kalshi",
            "display_name": "Kalshi",
            "role": "benchmark",
            "status": "ok" if quotes else ("error" if errors else "degraded"),
            "matches_count": len(quotes),
            "latency_ms": latency_ms,
            "message": "; ".join(errors[:2]) if errors else f"直連 Trade API v2 成功 ({len(quotes)} 場)",
        }
        return quotes, health

    @staticmethod
    def _mid_price(market: Dict[str, Any]) -> Optional[float]:
        try:
            bid = float(market.get("yes_bid_dollars") or 0)
            ask = float(market.get("yes_ask_dollars") or 0)
            last = float(market.get("last_price_dollars") or 0)
            if 0.01 <= bid <= 0.99 and 0.01 <= ask <= 0.99 and ask >= bid:
                # 價差太大 (>0.12) 代表沒流動性，改用 last 或忽略
                if (ask - bid) <= 0.12:
                    return (bid + ask) / 2.0
            if 0.01 <= last <= 0.99:
                return last
            if 0.01 <= ask <= 0.99:
                return ask
        except (TypeError, ValueError):
            pass
        return None

    def _parse_event(self, ev: Dict[str, Any], league: str, sport: str) -> Optional[SourceOddsQuote]:
        markets = ev.get("markets", [])
        if len(markets) < 2:
            return None

        # 二項勝敗或三項足球 (Win / Tie / Win)
        parsed_legs: List[Tuple[str, float]] = []
        close_time = ""
        for mk in markets:
            sub = (mk.get("yes_sub_title") or "").strip()
            p = self._mid_price(mk)
            if not sub or p is None:
                continue
            if not close_time:
                close_time = mk.get("expected_expiration_time") or mk.get("close_time") or ""
            parsed_legs.append((sub, p))

        if len(parsed_legs) not in (2, 3):
            return None

        # 若為 3 項 (如 EPL: TeamA, Tie, TeamB)，把 Draw 放到中間以對齊標準 [Home, Draw, Away]
        if len(parsed_legs) == 3:
            draws = [x for x in parsed_legs if "tie" in x[0].lower() or "draw" in x[0].lower()]
            teams = [x for x in parsed_legs if x not in draws]
            if len(teams) != 2 or len(draws) != 1:
                return None
            ordered = [teams[0], draws[0], teams[1]]
        else:
            ordered = parsed_legs

        names = [x[0] for x in ordered]
        raw_probs = [x[1] for x in ordered]
        dv = devig_power(raw_probs)
        raw_odds = [prob_to_decimal(p) for p in raw_probs]

        t1, t2 = names[0], names[-1]
        return SourceOddsQuote(
            source="kalshi",
            league=league,
            sport=sport,
            home_team=t1,
            away_team=t2,
            home_team_zh=get_zh_display_name(canonicalize_team(t1, league), t1),
            away_team_zh=get_zh_display_name(canonicalize_team(t2, league), t2),
            start_time=close_time,
            market_type="ML",
            outcome_names=names,
            raw_odds=raw_odds,
            true_probs=dv["true_probs"],
            fair_odds=dv["fair_odds"],
            vig_pct=dv["vig_pct"],
            match_url=f"https://kalshi.com/markets/{ev.get('series_ticker', '').lower()}/{ev.get('event_ticker', '').lower()}",
        )

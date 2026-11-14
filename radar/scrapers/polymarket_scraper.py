"""
1/5 參考指標：Polymarket 預測市場擷取器 (radar/scrapers/polymarket_scraper.py)
透過官方 Gamma API 擷取單場獨贏 (Moneyline / 3-Way) 與讓分 / 大小分合約，進行冪次去水。
"""
import time
from typing import List, Dict, Any, Optional
from sportsbet_agent.polymarket_client import PolymarketClient
from sportsbet_agent.proxy_config import get_active_proxy
from ..models import SourceOddsQuote
from ..devig import devig_power, prob_to_decimal
from ..matcher import canonicalize_team, get_zh_display_name


class PolymarketRadarScraper:
    def __init__(self, proxy_server: Optional[str] = "__AUTO__"):
        resolved = get_active_proxy() if proxy_server == "__AUTO__" else proxy_server
        self.client = PolymarketClient(proxy_server=resolved)

    def fetch_quotes(self, sport_filters: Optional[List[str]] = None) -> tuple[List[SourceOddsQuote], Dict[str, Any]]:
        t0 = time.time()
        quotes: List[SourceOddsQuote] = []
        filters = sport_filters or ["nba", "nfl", "nbl", "cs", "mlb", "epl", "ucl", "lol"]
        seen_slugs = set()

        errors = []
        for sf in filters:
            try:
                events = self.client.fetch_all_sports_matchups(sport_filter=sf)
                league = sf.upper()
                sport = self._map_sport(sf)
                for ev in events:
                    slug = ev.get("slug", "")
                    if not slug or slug in seen_slugs:
                        continue
                    seen_slugs.add(slug)
                    ml = ev.get("moneyline")
                    if not ml:
                        continue
                    outcomes = ml.get("outcomes", [])
                    prices = ml.get("prices", [])
                    if len(outcomes) < 2 or len(prices) < 2:
                        continue
                    # 過濾掉已完全收盤 (0.00 / 1.00) 或不合理價格
                    valid_p = [float(p) for p in prices[:3 if len(outcomes) == 3 else 2]]
                    if any(p <= 0.005 or p >= 0.995 for p in valid_p):
                        continue

                    dv = devig_power(valid_p)
                    raw_odds = [prob_to_decimal(p) for p in valid_p]
                    h_name = str(outcomes[0])
                    a_name = str(outcomes[-1])
                    quotes.append(SourceOddsQuote(
                        source="polymarket",
                        league=league,
                        sport=sport,
                        home_team=h_name,
                        away_team=a_name,
                        home_team_zh=get_zh_display_name(canonicalize_team(h_name, league), h_name),
                        away_team_zh=get_zh_display_name(canonicalize_team(a_name, league), a_name),
                        start_time=ev.get("start_date", ""),
                        market_type="ML",
                        outcome_names=outcomes[:len(valid_p)],
                        raw_odds=raw_odds,
                        true_probs=dv["true_probs"],
                        fair_odds=dv["fair_odds"],
                        vig_pct=dv["vig_pct"],
                        match_url=f"https://polymarket.com/event/{slug}",
                        extra={"volume_24h": ev.get("volume_24h", 0.0)},
                    ))
            except Exception as e:
                errors.append(f"{sf}: {e}")

        latency_ms = int((time.time() - t0) * 1000)
        health = {
            "source": "polymarket",
            "display_name": "Polymarket",
            "role": "benchmark",
            "status": "ok" if quotes else ("error" if errors else "degraded"),
            "matches_count": len(quotes),
            "latency_ms": latency_ms,
            "message": "; ".join(errors[:2]) if errors else f"已抓取 {len(quotes)} 場活躍合約",
        }
        return quotes, health

    @staticmethod
    def _map_sport(sf: str) -> str:
        s = sf.lower()
        if s in ("nba", "basketball", "nbl"):
            return "basketball"
        if s in ("nfl", "football"):
            return "football"
        if s in ("cs", "lol", "esports"):
            return "esports"
        if s in ("mlb", "baseball", "cpbl", "npb"):
            return "baseball"
        if s in ("epl", "ucl", "soccer", "laliga"):
            return "soccer"
        if s in ("nhl", "hockey"):
            return "hockey"
        return "other"

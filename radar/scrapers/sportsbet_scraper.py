"""
2/2 可投注目標盤口：澳洲 Sportsbet 公開盤口擷取器 (radar/scrapers/sportsbet_scraper.py)
只讀模式 (Read-Only)：無任何帳號登入、Cookie 或下單模組，透過 M1 AU 代理擷取即時賠率與讓分/大小。
"""
import concurrent.futures
import re
import time
from typing import List, Dict, Any, Tuple
from sportsbet_agent.query_sportsbet import fetch_sportsbet_matches
from ..models import SourceOddsQuote
from ..devig import devig_decimal_odds
from ..matcher import canonicalize_team, get_zh_display_name

SPORTSBET_QUERIES = [
    ("nba", "NBA", "basketball"),
    ("nfl", "NFL", "football"),
    ("nbl", "NBL", "basketball"),
    ("cs", "CS", "esports"),
    ("mlb", "MLB", "baseball"),
    ("cpbl", "CPBL", "baseball"),
    ("epl", "EPL", "soccer"),
    ("lol", "LOL", "esports"),
    ("nhl", "NHL", "hockey"),
]


class SportsbetRadarScraper:
    def _fetch_one(self, q_str: str, league: str, sport: str) -> Tuple[List[SourceOddsQuote], str]:
        out: List[SourceOddsQuote] = []
        try:
            raw_matches, route_info = fetch_sportsbet_matches(q_str, save_screenshot=False)
            for m in raw_matches:
                odds_list = m.get("odds", [])
                if len(odds_list) < 2:
                    continue
                try:
                    vals = [float(o["val"]) for o in odds_list]
                    names = [str(o["name"]) for o in odds_list]
                except (TypeError, ValueError):
                    continue
                if any(v <= 1.0 for v in vals):
                    continue

                t1 = str(m.get("team1") or names[0]).strip()
                t2 = str(m.get("team2") or names[-1]).strip()
                dv = devig_decimal_odds(vals, use_power=True)

                # 電競聯賽精確檢驗：避免 Sportsbet 在無 CS 盤口時導向一般電競而將 LoL (如 BLG/Gen.G) 或 eSoccer 誤標為 CS
                sub = (m.get("league") or "").lower()
                route_slug = (route_info.get("slug") or q_str).lower()
                detected_league = league
                if sport == "esports":
                    if any(k in sub for k in ["cs2", "counter-strike", "counter strike", "cs:go"]) or "cs " in sub:
                        detected_league = "CS"
                    elif any(k in sub for k in ["lol", "league of legends", "lck", "lpl", "worlds"]):
                        detected_league = "LOL"
                    elif any(k in sub for k in ["esoccer", "ebasketball", "dota"]):
                        detected_league = "OTHER"
                    elif "lol" in route_slug:
                        detected_league = "LOL"
                    elif "counter-strike" in route_slug:
                        detected_league = "CS"

                    # 嚴格過濾：若查詢目標為特定聯賽 (LOL 或 CS)，但賽事非該遊戲，則跳過避免污染
                    if league in ("LOL", "CS") and detected_league != league:
                        continue

                out.append(SourceOddsQuote(
                    source="sportsbet",
                    league=detected_league,
                    sport=sport,
                    home_team=t1,
                    away_team=t2,
                    home_team_zh=get_zh_display_name(canonicalize_team(t1, detected_league), t1),
                    away_team_zh=get_zh_display_name(canonicalize_team(t2, detected_league), t2),
                    start_time=str(m.get("time") or ""),
                    market_type="ML",
                    outcome_names=names,
                    raw_odds=vals,
                    true_probs=dv["true_probs"],
                    fair_odds=dv["fair_odds"],
                    vig_pct=dv["vig_pct"],
                    single_game_allowed=None,
                    match_url=f"https://www.sportsbet.com.au/betting/{route_info.get('slug', q_str)}",
                ))

                # 若有抓取到讓分 (Run Line / Handicap) 也納入比價
                for ex_str in m.get("extra", []):
                    ml_m = re.search(r"\(([+-]?[\d\.]+)\)\s*<code>([\d\.]+)</code>\s*/\s*\(([+-]?[\d\.]+)\)\s*<code>([\d\.]+)</code>", ex_str)
                    if ml_m:
                        line_1 = float(ml_m.group(1))
                        o_1 = float(ml_m.group(2))
                        o_2 = float(ml_m.group(4))
                        if o_1 > 1.0 and o_2 > 1.0:
                            dv_sp = devig_decimal_odds([o_1, o_2], use_power=True)
                            out.append(SourceOddsQuote(
                                source="sportsbet",
                                league=league,
                                sport=sport,
                                home_team=t1,
                                away_team=t2,
                                home_team_zh=get_zh_display_name(canonicalize_team(t1, league), t1),
                                away_team_zh=get_zh_display_name(canonicalize_team(t2, league), t2),
                                start_time=str(m.get("time") or ""),
                                market_type="SPREAD",
                                line=line_1,
                                outcome_names=[t1, t2],
                                raw_odds=[o_1, o_2],
                                true_probs=dv_sp["true_probs"],
                                fair_odds=dv_sp["fair_odds"],
                                vig_pct=dv_sp["vig_pct"],
                                single_game_allowed=None,
                                match_url=f"https://www.sportsbet.com.au/betting/{route_info.get('slug', q_str)}",
                            ))
            return out, ""
        except Exception as e:
            return out, f"{q_str}: {str(e)[:70]}"

    def fetch_quotes(self, queries: List[Tuple[str, str, str]] = None) -> Tuple[List[SourceOddsQuote], Dict[str, Any]]:
        t0 = time.time()
        quotes: List[SourceOddsQuote] = []
        errors: List[str] = []
        target_list = queries or SPORTSBET_QUERIES

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(self._fetch_one, q_str, league, sport) for q_str, league, sport in target_list]
            for fut in concurrent.futures.as_completed(futures):
                q_rows, err = fut.result()
                quotes.extend(q_rows)
                if err:
                    errors.append(err)

        latency_ms = int((time.time() - t0) * 1000)
        health = {
            "source": "sportsbet",
            "display_name": "澳洲 Sportsbet",
            "role": "target",
            "status": "ok" if quotes else ("error" if errors else "degraded"),
            "matches_count": len(quotes),
            "latency_ms": latency_ms,
            "message": "; ".join(errors[:2]) if errors else f"AU 代理只讀抓取 Sportsbet ({len(quotes)} 盤口)",
        }
        return quotes, health

"""
4/5 參考指標：Betfair Exchange (澳洲站) 免 API Key 公開盤口擷取器 (radar/scrapers/betfair_scraper.py)
透過 M1 澳洲代理呼叫 Betfair 公開導航與唯讀盤口 API，取得 Back/Lay 最佳報價並算出極低水真實勝率。
"""
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from curl_cffi import requests as creq
from sportsbet_agent.proxy_config import get_active_proxy
from ..models import SourceOddsQuote
from ..devig import devig_betfair_back_lay
from ..matcher import canonicalize_team, get_zh_display_name

# Betfair EventTypeId -> 運動類別
BETFAIR_TARGETS = [
    {"eventTypeId": 6423, "sport": "football", "league_keywords": {"NFL": "NFL"}},
    {"eventTypeId": 7522, "sport": "basketball", "league_keywords": {"NBA": "NBA", "Australian NBL": "NBL", "NBL": "NBL"}},
    {"eventTypeId": 1, "sport": "soccer", "league_keywords": {
        "English Premier League": "EPL",
        "Premier League": "EPL",
        "UEFA Champions League": "UCL",
        "Spanish La Liga": "LALIGA",
    }},
    {"eventTypeId": 7511, "sport": "baseball", "league_keywords": {"Major League Baseball": "MLB", "MLB": "MLB", "NPB": "NPB", "CPBL": "CPBL"}},
    {"eventTypeId": 7524, "sport": "hockey", "league_keywords": {"NHL": "NHL"}},
    {"eventTypeId": 27454571, "sport": "esports", "league_keywords": {
        "League of Legends": "LOL", "LoL": "LOL", "LCK": "LOL", "LPL": "LOL", "Worlds": "LOL",
        "Counter-Strike": "CS", "CS2": "CS", "CS:GO": "CS", "BLAST": "CS", "PGL": "CS", "IEM": "CS"
    }},
]


class BetfairRadarScraper:
    SEARCH_URL = "https://www.betfair.com.au/www/sports/navigation/facet/v1/search?_ak=nzIFcwyWhrlwYMrh&alt=json"
    BYMARKET_URL = "https://www.betfair.com.au/www/sports/exchange/readonly/v1/bymarket"

    def __init__(self, proxy_server: Optional[str] = "__AUTO__"):
        self.proxy_server = get_active_proxy() if proxy_server == "__AUTO__" else proxy_server
        self.proxies = {"http": self.proxy_server, "https": self.proxy_server} if self.proxy_server else None

    def fetch_quotes(self) -> Tuple[List[SourceOddsQuote], Dict[str, Any]]:
        t0 = time.time()
        quotes: List[SourceOddsQuote] = []
        errors: List[str] = []

        for cfg in BETFAIR_TARGETS:
            try:
                quotes.extend(self._fetch_event_type(cfg))
            except Exception as e:
                errors.append(f"{cfg['sport']}: {str(e)[:80]}")

        latency_ms = int((time.time() - t0) * 1000)
        health = {
            "source": "betfair",
            "display_name": "Betfair Exchange (AU)",
            "role": "benchmark",
            "status": "ok" if quotes else ("error" if errors else "degraded"),
            "matches_count": len(quotes),
            "latency_ms": latency_ms,
            "message": "; ".join(errors[:2]) if errors else f"AU 代理直連 Betfair Exchange ({len(quotes)} 場)",
        }
        return quotes, health

    def _fetch_event_type(self, cfg: Dict[str, Any]) -> List[SourceOddsQuote]:
        payload = {
            "filter": {
                "eventTypeIds": [cfg["eventTypeId"]],
                "marketTypeCodes": ["MONEY_LINE", "MATCH_ODDS"],
            },
            "facets": [{"type": "COMPETITION", "maxValues": 30}],
            "maxResults": 80,
            "marketProjection": ["MARKET_START_TIME", "EVENT", "COMPETITION"],
        }
        rs = creq.post(
            self.SEARCH_URL,
            json=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            impersonate="chrome",
            proxies=self.proxies,
            timeout=10,
        )
        if rs.status_code != 200:
            return []

        data = rs.json()
        comp_map = {}
        for cid, cobj in (data.get("attachments", {}).get("competitions") or {}).items():
            comp_map[str(cid)] = cobj.get("name", "")

        # 篩選屬於目標聯賽之 marketIds (若 competitions 未展開則抓前 25 筆在 bymarket 內再以 eventName/market 檢查)
        target_mids: List[Tuple[str, str]] = []
        for item in data.get("results", []):
            mid = item.get("marketId")
            cid = str(item.get("competitionId", ""))
            cname = comp_map.get(cid, "")
            matched_league = None
            for kw, code in cfg["league_keywords"].items():
                if kw.lower() in cname.lower():
                    matched_league = code
                    break
            if mid and (matched_league or not comp_map):
                target_mids.append((mid, matched_league or list(cfg["league_keywords"].values())[0]))

        if not target_mids:
            return []

        quotes: List[SourceOddsQuote] = []
        # 每次 batch 最多 20 個 marketIds
        for i in range(0, min(len(target_mids), 40), 20):
            batch = target_mids[i:i + 20]
            mid_to_league = dict(batch)
            mids_str = ",".join(m[0] for m in batch)
            params = {
                "_ak": "nzIFcwyWhrlwYMrh",
                "alt": "json",
                "currencyCode": "AUD",
                "locale": "en_AU",
                "marketIds": mids_str,
                "types": "MARKET_STATE,MARKET_DESCRIPTION,EVENT,RUNNER_DESCRIPTION,RUNNER_EXCHANGE_PRICES_BEST",
            }
            rm = creq.get(
                self.BYMARKET_URL,
                params=params,
                impersonate="chrome",
                proxies=self.proxies,
                timeout=10,
            )
            if rm.status_code != 200:
                continue
            bm_data = rm.json()
            for et in bm_data.get("eventTypes", []):
                for ev_node in et.get("eventNodes", []):
                    ev_info = ev_node.get("event", {})
                    ev_name = ev_info.get("eventName", "")
                    open_date = ev_info.get("openDate", "")
                    for mk_node in ev_node.get("marketNodes", []):
                        mid = mk_node.get("marketId", "")
                        state = mk_node.get("state", {})
                        if state.get("status") != "OPEN":
                            continue
                        runners = mk_node.get("runners", [])
                        if len(runners) not in (2, 3):
                            continue

                        # 解析隊名順序
                        q = self._parse_market_node(
                            runners=runners,
                            ev_name=ev_name,
                            open_date=open_date,
                            league=mid_to_league.get(mid, list(cfg["league_keywords"].values())[0]),
                            sport=cfg["sport"],
                            is_live=bool(state.get("inplay")),
                            total_matched=float(state.get("totalMatched") or 0),
                            market_id=mid,
                        )
                        if q:
                            quotes.append(q)
        return quotes

    @staticmethod
    def _parse_market_node(
        runners: List[Dict[str, Any]],
        ev_name: str,
        open_date: str,
        league: str,
        sport: str,
        is_live: bool,
        total_matched: float,
        market_id: str,
    ) -> Optional[SourceOddsQuote]:
        names: List[str] = []
        backs: List[Optional[float]] = []
        lays: List[Optional[float]] = []

        for r in runners:
            rname = (r.get("description") or {}).get("runnerName", "").strip()
            ex = r.get("exchange") or {}
            b_list = ex.get("availableToBack") or []
            l_list = ex.get("availableToLay") or []
            b_price = float(b_list[0]["price"]) if b_list else None
            l_price = float(l_list[0]["price"]) if l_list else None
            if not rname or (b_price is None and l_price is None):
                return None
            names.append(rname)
            backs.append(b_price)
            lays.append(l_price)

        # Betfair 3-way 順序通常是 [Home, Away, The Draw]，標準化為 [Home, Draw, Away]
        if len(names) == 3:
            draw_idx = next((idx for idx, n in enumerate(names) if "draw" in n.lower()), None)
            if draw_idx is not None and draw_idx != 1:
                other = [i for i in range(3) if i != draw_idx]
                order = [other[0], draw_idx, other[1]]
                names = [names[i] for i in order]
                backs = [backs[i] for i in order]
                lays = [lays[i] for i in order]

        dv = devig_betfair_back_lay(backs, lays)
        if not dv.get("is_valid", True):
            return None

        # 水錢過高 (正常 Betfair 交易所水錢在 -2% ~ +5% 之間，若 > 10% 必為流動性枯竭廢單)
        if dv["vig_pct"] > 10.0 or dv["vig_pct"] < -5.0:
            return None

        raw_odds = [round(b if b else (l or 0.0), 3) for b, l in zip(backs, lays)]
        if any(o <= 1.0 for o in raw_odds):
            return None

        # 非滾球賽事若出現極端賠率 (如 <= 1.02)，多為散戶亂掛撿便宜單，直接過濾
        if not is_live and any(o <= 1.02 for o in raw_odds):
            return None

        # 解析 Betfair 事件名稱順序 (通常為 "Away @ Home" 美盤 或 "Home v Away")
        h_name, a_name = names[0], names[-1]
        if " @ " in ev_name:
            parts = [p.strip() for p in ev_name.split(" @ ", 1)]
            if len(parts) == 2:
                a_name, h_name = parts[0], parts[1]
        elif " v " in ev_name:
            parts = [p.strip() for p in ev_name.split(" v ", 1)]
            if len(parts) == 2:
                h_name, a_name = parts[0], parts[1]

        # 核心對齊修復：將 names、raw_odds、true_probs、fair_odds 嚴格重排為 [Home, Away] (或 3-way [Home, Draw, Away])
        # 確保 index 0 永遠對應 home_team，index 1 (或最後) 永遠對應 away_team，徹底杜絕賠率與隊伍反置
        true_probs = dv["true_probs"]
        fair_odds = dv["fair_odds"]

        def _name_matches(cand: str, target: str) -> bool:
            c, t = cand.lower().strip(), target.lower().strip()
            return c == t or c in t or t in c

        if len(names) == 2:
            if _name_matches(names[0], a_name) or _name_matches(names[1], h_name):
                order = [1, 0]
            else:
                order = [0, 1]
            names = [names[i] for i in order]
            raw_odds = [raw_odds[i] for i in order]
            true_probs = [true_probs[i] for i in order]
            fair_odds = [fair_odds[i] for i in order]
        elif len(names) == 3:
            draw_idx = next((i for i, n in enumerate(names) if "draw" in n.lower()), 1)
            other = [i for i in range(3) if i != draw_idx]
            if _name_matches(names[other[0]], a_name) or _name_matches(names[other[1]], h_name):
                h_idx, a_idx = other[1], other[0]
            else:
                h_idx, a_idx = other[0], other[1]
            order = [h_idx, draw_idx, a_idx]
            names = [names[i] for i in order]
            raw_odds = [raw_odds[i] for i in order]
            true_probs = [true_probs[i] for i in order]
            fair_odds = [fair_odds[i] for i in order]

        return SourceOddsQuote(
            source="betfair",
            league=league,
            sport=sport,
            home_team=h_name,
            away_team=a_name,
            home_team_zh=get_zh_display_name(canonicalize_team(h_name, league), h_name),
            away_team_zh=get_zh_display_name(canonicalize_team(a_name, league), a_name),
            start_time=open_date,
            market_type="ML",
            outcome_names=names,
            raw_odds=raw_odds,
            true_probs=true_probs,
            fair_odds=fair_odds,
            vig_pct=dv["vig_pct"],
            is_live=is_live,
            match_url=f"https://www.betfair.com.au/exchange/plus/market/{market_id}",
            extra={"total_matched_aud": round(total_matched, 2), "event_name": ev_name},
        )

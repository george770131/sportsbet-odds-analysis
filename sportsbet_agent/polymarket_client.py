#!/usr/bin/env python3
"""
Polymarket 行情與預測市場資料擷取模組 (polymarket_client.py)
-----------------------------------------------------------------------------
功能：
1. 透過官方 Gamma API 擷取目前在 Polymarket 上熱門且活躍之體育賽事與電競盤口。
2. 支援代理伺服器 (讀取 config.json 之 proxy_server)。
3. 提取二項獨贏 (Moneyline / Head-to-Head)、讓分 (Spread)、大小分 (Over/Under) 盤口。
4. 解析即時交易價格 (Prices)、成交量 (Volume) 與流動性 (Liquidity)。
-----------------------------------------------------------------------------
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.parse

try:
    from .proxy_config import get_active_proxy
except ImportError:
    from proxy_config import get_active_proxy

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"

DEFAULT_PROXY = get_active_proxy()


class PolymarketClient:
    GAMMA_BASE_URL = "https://gamma-api.polymarket.com"

    # Polymarket 常用 Tag ID
    TAG_GAMES = 100639       # 單場即時賽事 (Match Games)
    TAG_SPORTS = 1           # 體育全域
    TAG_NBA = 745            # 美國職籃 NBA
    TAG_LOL = 65             # 英雄聯盟 LoL
    TAG_EPL = 306            # 英超 Premier League
    TAG_UCL = 1234           # 歐冠 UEFA Champions League
    TAG_MLB = 100381         # 美國職棒 MLB

    SPORT_TAGS = {
        "nba": 745,
        "basketball": 745,
        "nfl": 451,
        "cs": 100780,
        "cs2": 100780,
        "lol": 65,
        "esports": 65,
        "worlds": 65,
        "epl": 306,
        "premier": 306,
        "soccer": 306,
        "ucl": 1234,
        "mlb": 100381,
        "baseball": 100381
    }

    def __init__(self, proxy_server: Optional[str] = DEFAULT_PROXY):
        self.proxy_server = proxy_server
        self._session = None
        if HAS_REQUESTS:
            self._session = requests.Session()
            if self.proxy_server:
                self._session.proxies = {
                    "http": self.proxy_server,
                    "https": self.proxy_server
                }
            self._session.headers.update({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            })
        else:
            handlers = []
            if self.proxy_server:
                handlers.append(urllib.request.ProxyHandler({
                    "http": self.proxy_server,
                    "https": self.proxy_server
                }))
            self._opener = urllib.request.build_opener(*handlers)

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: int = 15) -> Any:
        url = f"{self.GAMMA_BASE_URL}{endpoint}"
        if HAS_REQUESTS and self._session:
            resp = self._session.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        else:
            if params:
                qs = urllib.parse.urlencode(params)
                url = f"{url}?{qs}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json"
                }
            )
            with self._opener.open(req, timeout=timeout) as resp:
                content = resp.read().decode("utf-8")
                return json.loads(content)

    def get_active_games(self, tag_id: Optional[int] = None, limit: int = 15, order: str = "volume24hr", ascending: bool = False) -> List[Dict]:
        """獲取特定 Tag 或單場比賽的活躍事件"""
        target_tag = tag_id if tag_id is not None else self.TAG_GAMES
        params = {
            "active": "true",
            "closed": "false",
            "tag_id": target_tag,
            "order": order,
            "ascending": "true" if ascending else "false",
            "limit": limit
        }
        try:
            events = self._get("/events", params=params, timeout=12)
            return events if isinstance(events, list) else []
        except Exception as e:
            print(f"[PolymarketClient] 擷取賽事 (tag {target_tag}) 失敗: {e}")
            return []

    def get_events_by_slug(self, slug: str) -> List[Dict]:
        """依據 Slug 查詢特定事件"""
        try:
            return self._get("/events", params={"slug": slug}, timeout=12)
        except Exception as e:
            print(f"[PolymarketClient] 依 Slug 查詢失敗: {e}")
            return []

    def parse_market_prices(self, market: Dict) -> Dict:
        """安全解析 Polymarket market 中的 outcomes 與 prices"""
        raw_outcomes = market.get("outcomes", [])
        if isinstance(raw_outcomes, str):
            try:
                raw_outcomes = json.loads(raw_outcomes)
            except Exception:
                raw_outcomes = []

        raw_prices = market.get("outcomePrices", [])
        if isinstance(raw_prices, str):
            try:
                raw_prices = json.loads(raw_prices)
            except Exception:
                raw_prices = []

        prices_float = []
        for p in raw_prices:
            try:
                prices_float.append(float(p))
            except (ValueError, TypeError):
                prices_float.append(0.0)

        return {
            "question": market.get("question", ""),
            "groupItemTitle": market.get("groupItemTitle"),
            "outcomes": raw_outcomes,
            "prices": prices_float,
            "volume": float(market.get("volume", 0.0) or 0.0),
            "liquidity": float(market.get("liquidity", 0.0) or 0.0),
            "clobTokenIds": market.get("clobTokenIds", [])
        }

    def extract_structured_match(self, event: Dict) -> Optional[Dict]:
        """將 Polymarket 的 Event 結構化為統一的對戰盤口資料"""
        title = event.get("title", "")
        slug = event.get("slug", "")
        markets = event.get("markets", [])
        if not markets:
            return None

        # 辨識球種/賽事類別
        sport_category = "General"
        tags = [t.get("label", "").lower() for t in event.get("tags", []) if isinstance(t, dict)]
        if any("nba" in t or "basketball" in t for t in tags):
            if any("nbl" in t for t in tags):
                sport_category = "NBL"
            else:
                sport_category = "NBA"
        elif any("cs2" in t or "counter strike" in t or "counter-strike" in t or "cs:go" in t for t in tags) or "cs2-" in slug or "cs-" in slug:
            sport_category = "CS"
        elif any("lol" in t or "league of legends" in t for t in tags) or "lol-" in slug:
            sport_category = "LoL"
        elif any("mlb" in t or "baseball" in t for t in tags):
            sport_category = "MLB"
        elif any("nfl" in t or "american-football" in t for t in tags):
            sport_category = "NFL"
        elif any("soccer" in t or "premier" in t or "uefa" in t for t in tags):
            sport_category = "Soccer"
        elif any("tennis" in t or "wta" in t or "atp" in t for t in tags):
            sport_category = "Tennis"

        # 尋找獨贏盤 (Moneyline)
        moneyline_market = None
        spread_markets = []
        total_markets = []

        for m in markets:
            parsed = self.parse_market_prices(m)
            q = parsed["question"]
            git = parsed["groupItemTitle"]

            if git is None and (" vs. " in q or " vs " in q or " v " in q) and "O/U" not in q and "Spread" not in q:
                if len(parsed["outcomes"]) == 2:
                    moneyline_market = parsed
            elif git and "Spread" in git:
                spread_markets.append(parsed)
            elif "O/U" in q or "Total" in q:
                total_markets.append(parsed)

        # 若未直接找到 moneyline，但第一個 market 是 2 個選項的對戰
        if not moneyline_market and markets:
            first_m = self.parse_market_prices(markets[0])
            if len(first_m["outcomes"]) == 2 and "O/U" not in first_m["question"] and "Spread" not in first_m["question"]:
                moneyline_market = first_m

        if not moneyline_market:
            return None

        return {
            "id": event.get("id"),
            "title": title,
            "slug": slug,
            "sport": sport_category,
            "volume_24h": float(event.get("volume24hr", 0.0) or 0.0),
            "liquidity": float(event.get("liquidity", 0.0) or 0.0),
            "moneyline": moneyline_market,
            "spreads_count": len(spread_markets),
            "totals_count": len(total_markets),
            "tags": tags
        }

    def fetch_all_sports_matchups(self, sport_filter: Optional[str] = None) -> List[Dict]:
        """擷取並結構化所有當前可投注之比賽"""
        events_pool = []
        seen_ids = set()

        # 1. 優先查詢指定球種專屬 Tag (若有)
        if sport_filter:
            sf_clean = sport_filter.lower().strip()
            if sf_clean in self.SPORT_TAGS:
                tag_id = self.SPORT_TAGS[sf_clean]
                sport_events = self.get_active_games(tag_id=tag_id, limit=12)
                for ev in sport_events:
                    eid = ev.get("id")
                    if eid not in seen_ids:
                        seen_ids.add(eid)
                        events_pool.append(ev)

        # 2. 獲取單場合約 (TAG_GAMES) 熱門前 15 場
        games_events = self.get_active_games(tag_id=self.TAG_GAMES, limit=15)
        for ev in games_events:
            eid = ev.get("id")
            if eid not in seen_ids:
                seen_ids.add(eid)
                events_pool.append(ev)

        structured = []
        for ev in events_pool:
            match = self.extract_structured_match(ev)
            if match:
                if sport_filter:
                    if sport_filter.upper() not in match["sport"].upper():
                        continue
                structured.append(match)
        return structured


if __name__ == "__main__":
    client = PolymarketClient()
    print("🌐 正在自 Polymarket 擷取即時體育/電競賽事...")
    matches = client.fetch_all_sports_matchups()
    print(f"✅ 成功擷取並結構化 {len(matches)} 場對戰盤口：\n")
    for i, m in enumerate(matches[:10], 1):
        ml = m["moneyline"]
        teams = ml["outcomes"]
        prices = ml["prices"]
        vol = m["volume_24h"]
        odds_repr = " / ".join([f"{t}: ${p:.3f}" for t, p in zip(teams, prices)])
        print(f"[{m['sport']}] {i}. {m['title']}")
        print(f"    • 獨贏盤 (Moneyline)：{odds_repr}")
        print(f"    • 24小時成交量：${vol:,.0f} USD ｜ Slug: {m['slug']}\n")

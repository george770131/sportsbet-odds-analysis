"""
背景 7 平台賠率採集與 Telegram +EV 推播排程器 (radar/collector.py)
支援單次觸發 (`--once`) 與 24/7 常駐輪詢模式 (由 M1 PM2 託管)
"""
import argparse
import concurrent.futures
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Any, Tuple
import config
from sportsbet_agent.proxy_config import load_agent_config
from .models import SourceOddsQuote
from .database import radar_db
from .engine import OddsComparisonEngine
from .scrapers.polymarket_scraper import PolymarketRadarScraper
from .scrapers.kalshi_scraper import KalshiRadarScraper
from .scrapers.pinnacle_scraper import PinnacleRadarScraper
from .scrapers.betfair_scraper import BetfairRadarScraper
from .scrapers.bet365_oddsportal_scraper import Bet365OddsportalRadarScraper
from .scrapers.tsl_scraper import TSLRadarScraper
from .scrapers.sportsbet_scraper import SportsbetRadarScraper


class RadarCollector:
    def __init__(self, include_playwright: bool = True):
        self.include_playwright = include_playwright
        self.engine = OddsComparisonEngine()
        # 避免重複推播同一張高 +EV 卡片 (card_id -> last_sent_ts)
        self._alerted_cache: Dict[str, float] = {}

    def run_once(self) -> Dict[str, Any]:
        t_start = time.time()
        all_quotes: List[SourceOddsQuote] = []
        health_rows: List[Dict[str, Any]] = []
        now_str = config.get_taiwan_now_str("%Y-%m-%d %H:%M:%S")

        tasks = {
            "polymarket": lambda: PolymarketRadarScraper().fetch_quotes(),
            "kalshi": lambda: KalshiRadarScraper().fetch_quotes(),
            "pinnacle": lambda: PinnacleRadarScraper().fetch_quotes(),
            "betfair": lambda: BetfairRadarScraper().fetch_quotes(),
            "tsl": lambda: TSLRadarScraper().fetch_quotes(),
        }
        if self.include_playwright:
            tasks["bet365"] = lambda: Bet365OddsportalRadarScraper().fetch_quotes(max_total_matches=10)
            tasks["sportsbet"] = lambda: SportsbetRadarScraper().fetch_quotes()

        # 平行抓取以將總採集耗時壓到最低
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            futures = {pool.submit(fn): name for name, fn in tasks.items()}
            for fut in concurrent.futures.as_completed(futures):
                name = futures[fut]
                try:
                    quotes, health = fut.result(timeout=120)
                    all_quotes.extend(quotes)
                    health["updated_at"] = now_str
                    health_rows.append(health)
                except Exception as e:
                    health_rows.append({
                        "source": name,
                        "display_name": name,
                        "role": "target" if name in ("tsl", "sportsbet") else "benchmark",
                        "status": "error",
                        "matches_count": 0,
                        "latency_ms": 0,
                        "message": str(e)[:120],
                        "updated_at": now_str,
                    })

        cards = self.engine.align_and_evaluate(all_quotes, min_benchmarks=1)
        radar_db.replace_comparisons(cards)
        radar_db.upsert_source_health(health_rows)
        elapsed = round(time.time() - t_start, 2)
        radar_db.set_meta("last_sync_at", now_str, now_str)
        radar_db.set_meta("last_sync_elapsed_sec", str(elapsed), now_str)
        radar_db.set_meta("total_cards", str(len(cards)), now_str)
        pos_cards = [c for c in cards if c["is_positive_ev"]]
        radar_db.set_meta("positive_ev_cards", str(len(pos_cards)), now_str)

        # 自動推播高價值 +EV (預設 >= 4.0% 且至少 2 家參考指標確認)
        alerts_sent = self._dispatch_telegram_alerts(pos_cards)

        return {
            "synced_at": now_str,
            "elapsed_sec": elapsed,
            "raw_quotes_count": len(all_quotes),
            "aligned_cards_count": len(cards),
            "positive_ev_count": len(pos_cards),
            "alerts_sent": alerts_sent,
            "health": health_rows,
        }

    def _dispatch_telegram_alerts(self, pos_cards: List[Dict[str, Any]], min_ev: float = 4.0, min_bench: int = 2) -> int:
        cfg = load_agent_config()
        token = cfg.get("telegram_bot_token")
        chat_id = cfg.get("allowed_chat_id")
        if not token or not chat_id:
            return 0

        now_ts = time.time()
        to_send = []
        for c in pos_cards:
            if c["ev_pct"] < min_ev or c["valid_benchmark_count"] < min_bench:
                continue
            last_ts = self._alerted_cache.get(c["card_id"], 0.0)
            # 同一盤口 45 分鐘內不重複轟炸
            if now_ts - last_ts < 2700:
                continue
            self._alerted_cache[c["card_id"]] = now_ts
            to_send.append(c)

        if not to_send:
            return 0

        lines = ["📡 <b>7平台比價雷達｜發現正期望值 (+EV)</b>\n"]
        for c in to_send[:5]:
            parlay_tag = " ⚠️<b>需串關</b>" if c.get("single_game_allowed") is False else (
                " ✅單場" if c.get("single_game_allowed") is True else ""
            )
            mkt_label = {"ML": "獨贏", "SPREAD": f"讓分 {c['line_display']}", "TOTAL": f"大小 {c['line_display']}"}.get(c["market_type"], c["market_type"])
            lines.append(
                f"• <b>[{c['league']}] {c['away_team_zh']} @ {c['home_team_zh']}</b> ({mkt_label})\n"
                f"  🎯 <b>{c['target_book_name']}</b> 買 <b>{c['selection_name']}</b> @ <code>{c['target_odds']}</code>{parlay_tag}\n"
                f"  📊 共識真勝率 <code>{round(c['consensus_prob']*100, 1)}%</code> (公平 {c['consensus_fair_odds']}) ｜ "
                f"<b>+{c['ev_pct']}% EV</b> ｜ 有效參考：<code>{c['valid_benchmark_count']}/5</code>"
            )

        msg = "\n".join(lines)
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = urllib.parse.urlencode({"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            urllib.request.urlopen(req, timeout=8)
            return len(to_send[:5])
        except Exception:
            return 0


def main():
    parser = argparse.ArgumentParser(description="7-Platform Read-Only Odds Radar Collector")
    parser.add_argument("--once", action="store_true", help="僅執行單次採集並退出")
    parser.add_argument("--interval", type=int, default=180, help="輪詢間隔秒數 (預設 180 秒)")
    parser.add_argument("--fast", action="store_true", help="略過 Playwright (Bet365/Sportsbet)，僅抓 API 來源測試")
    args = parser.parse_args()

    collector = RadarCollector(include_playwright=not args.fast)
    if args.once:
        res = collector.run_once()
        print(f"✅ 單次採集完成 ({res['elapsed_sec']}s)｜原始盤口: {res['raw_quotes_count']}｜對齊卡片: {res['aligned_cards_count']}｜+EV 機會: {res['positive_ev_count']}")
        for h in res["health"]:
            print(f"   • {h['display_name']}: [{h['status']}] {h['matches_count']} 筆 ({h['latency_ms']}ms) - {h['message']}")
        return

    print(f"🔄 啟動 24/7 背景賠率採集服務 (間隔 {args.interval}s)...")
    while True:
        try:
            res = collector.run_once()
            print(f"[{res['synced_at']}] 採集完成 ({res['elapsed_sec']}s)｜對齊: {res['aligned_cards_count']}｜+EV: {res['positive_ev_count']}")
        except Exception as e:
            print(f"[Collector Error] {e}")
        time.sleep(max(30, args.interval))


if __name__ == "__main__":
    main()

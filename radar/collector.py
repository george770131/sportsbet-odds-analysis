"""
背景 7 平台賠率採集與 Telegram +EV 推播排程器 (radar/collector.py)
支援單次觸發 (`--once`) 與 24/7 常駐輪詢模式 (由 M1 PM2 託管)
"""
import argparse
import concurrent.futures
import html
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
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
        # 避免重複轟炸同一張 +EV 卡片: card_id -> (last_sent_ts, last_ev_pct, last_odds)
        self._alerted_cache: Dict[str, Tuple[float, float, float]] = {}

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

        # 只要發現高信心正 +EV (ev_pct >= +2.0%, 共識勝率 40%~80%, 至少 3/5 家參考指標且台彩非需串關) 即立即推播完整 7 平台明細卡片至 Telegram
        alerts_sent = self._dispatch_telegram_alerts(
            pos_cards,
            min_ev=2.0,
            min_bench=3,
            min_prob=0.40,
            max_prob=0.80,
        )

        return {
            "synced_at": now_str,
            "elapsed_sec": elapsed,
            "raw_quotes_count": len(all_quotes),
            "aligned_cards_count": len(cards),
            "positive_ev_count": len(pos_cards),
            "alerts_sent": alerts_sent,
            "health": health_rows,
        }

    @staticmethod
    def _side_index(card: Dict[str, Any]) -> int:
        side = card.get("selection_side", "home")
        if side in ("home", "over"):
            return 0
        if side == "draw":
            return 1
        t_book = card.get("target_book", "")
        raw = card.get("targets", {}).get(t_book, {}).get("raw_odds", [])
        return 2 if len(raw) == 3 else 1

    @staticmethod
    def _get_latest_tunnel_url() -> str:
        log_path = Path.home() / ".pm2" / "logs" / "odds-tunnel-out.log"
        if not log_path.exists():
            return ""
        try:
            text = log_path.read_text(encoding="utf-8", errors="ignore")
            matches = re.findall(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", text)
            return matches[-1] if matches else ""
        except Exception:
            return ""

    @classmethod
    def format_telegram_card(cls, c: Dict[str, Any], tunnel_url: str = "") -> str:
        idx = cls._side_index(c)
        mkt_label = {
            "ML": "獨贏 ML",
            "SPREAD": f"讓分 {c.get('line_display', '')}",
            "TOTAL": f"大小 {c.get('line_display', '')}",
        }.get(c.get("market_type", ""), c.get("market_type", ""))

        parlay_tag = ""
        if c.get("target_book") == "tsl":
            if c.get("single_game_allowed") is False:
                parlay_tag = " ⚠️<b>需串關</b>"
            elif c.get("single_game_allowed") is True:
                parlay_tag = " ✅單場可下"

        away_zh = html.escape(str(c.get("away_team_zh", "")))
        home_zh = html.escape(str(c.get("home_team_zh", "")))
        away_en = html.escape(str(c.get("away_team", "")))
        home_en = html.escape(str(c.get("home_team", "")))
        sel_name = html.escape(str(c.get("selection_name", "")))
        book_name = html.escape(str(c.get("target_book_name", "")))
        start_tw = html.escape(str(c.get("start_time_tw", "近期開賽")))
        league = html.escape(str(c.get("league", "")))

        lines = [
            f"🟢 <b>發現正期望值 +EV（+{c['ev_pct']:.2f}% EV）</b>",
            f"<b>[{league}] {html.escape(mkt_label)}</b>｜{start_tw}｜有效參考家數：<b>{c['valid_benchmark_count']}/{c.get('total_benchmarks', 5)}</b>",
            "",
            f"🏟️ <b>{away_zh} @ {home_zh}</b>",
            f"<i>{away_en} @ {home_en}</i>",
            "",
            f"🎯 <b>{book_name}</b>{parlay_tag} 買 <b>{sel_name}</b>｜可下賠率 <b><code>{c['target_odds']:.2f}</code></b>",
            f"📊 指標共識真勝率 <code>{c['consensus_prob']*100:.1f}%</code> · 公平賠率 <code>{c['consensus_fair_odds']:.2f}</code> · 勝率優勢 <code>+{c['edge_pct']:.1f}%</code>",
            "",
            "<b>7 平台獨立去水明細（賠率｜水錢｜去水勝率）</b>",
        ]

        benchmarks = c.get("benchmarks", {})
        for b_key, label in [
            ("pinnacle", "Pinnacle"),
            ("betfair", "Betfair Exchange"),
            ("polymarket", "Polymarket"),
            ("kalshi", "Kalshi"),
            ("bet365", "Bet365"),
        ]:
            info = benchmarks.get(b_key, {})
            url = info.get("url")
            link_label = f'<a href="{url}">{label}</a>' if url else label
            if info.get("available") and len(info.get("raw_odds", [])) > idx:
                raw_o = info["raw_odds"][idx]
                vig = info.get("vig_pct", 0.0)
                prob = info["true_probs_pct"][idx]
                lines.append(f"• {link_label} [指標]：<code>{raw_o:.2f}</code>｜<code>{vig:.1f}%</code>｜<b><code>{prob:.1f}%</code></b>")
            else:
                lines.append(f"• {link_label} [指標]：未開盤")

        targets = c.get("targets", {})
        for t_key, label in [
            ("tsl", "🇹🇼 台灣運彩"),
            ("sportsbet", "🇦🇺 澳洲 Sportsbet"),
        ]:
            info = targets.get(t_key, {})
            url = info.get("url")
            link_label = f'<a href="{url}"><b>{label}</b></a>' if url else f'<b>{label}</b>'
            if info.get("available") and len(info.get("raw_odds", [])) > idx:
                raw_o = info["raw_odds"][idx]
                vig = info.get("vig_pct", 0.0)
                probs = info.get("true_probs_pct", [])
                if len(probs) > idx:
                    prob_str = f"{probs[idx]:.1f}%"
                else:
                    odds_arr = info.get("raw_odds", [])
                    sum_inv = sum((1.0 / o) for o in odds_arr if o and o > 1.0)
                    prob_str = f"{((1.0 / raw_o) / sum_inv) * 100.0:.1f}%" if sum_inv > 0 and raw_o > 1.0 else "—"
                extra_tag = ""
                if t_key == "tsl":
                    if info.get("single_game_allowed") is False:
                        extra_tag = " ⚠️需串關"
                    elif info.get("single_game_allowed") is True:
                        extra_tag = " 單場"
                lines.append(f"• {link_label} [可投{extra_tag}]：<b><code>{raw_o:.2f}</code></b>｜<code>{vig:.1f}%</code>｜<b><code>{prob_str}</code></b>")
            else:
                lines.append(f"• {link_label} [可投]：未開盤")

        if tunnel_url:
            lines.append(f"\n📱 <a href=\"{tunnel_url}\">點此開啟 7 盤定量比價雷達</a>")
        return "\n".join(lines)

    def _dispatch_telegram_alerts(
        self,
        pos_cards: List[Dict[str, Any]],
        min_ev: float = 2.0,
        min_bench: int = 3,
        min_prob: float = 0.40,
        max_prob: float = 0.80,
    ) -> int:
        cfg = load_agent_config()
        token = cfg.get("telegram_bot_token")
        chat_id = cfg.get("allowed_chat_id")
        if not token or not chat_id:
            return 0

        now_ts = time.time()
        # 清理超過 1 小時的舊快取
        self._alerted_cache = {k: v for k, v in self._alerted_cache.items() if now_ts - v[0] < 3600}

        to_send = []
        for c in pos_cards:
            # 1. 期望值必須 >= min_ev (+2.0%) 且有效參考家數必須 >= min_bench (3/5)
            if c["ev_pct"] < min_ev or c["valid_benchmark_count"] < min_bench:
                continue

            # 2. 共識預估勝率必須在 40% ~ 80% 之間 (0.40 <= consensus_prob <= 0.80)
            prob = float(c.get("consensus_prob", 0.0))
            if round(prob, 4) < min_prob or round(prob, 4) > max_prob:
                continue

            # 3. 台灣運彩若為「需串關」盤口，不發送 Telegram 訊息 (僅在網頁端保留供手動檢視)
            if c.get("target_book") == "tsl" and (c.get("single_game_allowed") is False or c.get("min_parlay_legs", 1) > 1):
                continue

            prev = self._alerted_cache.get(c["card_id"])
            if prev:
                last_ts, last_ev, last_odds = prev
                # 30 分鐘內同一盤口若賠率沒變好、EV 也沒有大幅躍升 (+1.0% 以上) 則不重複轟炸
                improved = (c["target_odds"] > last_odds) and (c["ev_pct"] >= last_ev + 1.0)
                if (now_ts - last_ts < 1800) and not improved:
                    continue
            self._alerted_cache[c["card_id"]] = (now_ts, float(c["ev_pct"]), float(c["target_odds"]))
            to_send.append(c)

        if not to_send:
            return 0

        tunnel_url = self._get_latest_tunnel_url()
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        sent = 0
        for c in to_send[:5]:
            msg = self.format_telegram_card(c, tunnel_url=tunnel_url)
            try:
                data = urllib.parse.urlencode({
                    "chat_id": chat_id,
                    "text": msg,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": "true",
                }).encode()
                req = urllib.request.Request(url, data=data, method="POST")
                urllib.request.urlopen(req, timeout=8)
                sent += 1
                time.sleep(0.3)
            except Exception:
                continue
        return sent


def main():
    parser = argparse.ArgumentParser(description="7-Platform Read-Only Odds Radar Collector")
    parser.add_argument("--once", action="store_true", help="僅執行單次採集並退出")
    parser.add_argument("--interval", type=int, default=120, help="輪詢間隔秒數 (預設 120 秒)")
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

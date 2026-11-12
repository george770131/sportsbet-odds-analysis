#!/usr/bin/env python3
"""
Sportsbet vs Polymarket 跨市場量化比價與金礦雷達 (market_comparator.py)
-----------------------------------------------------------------------------
功能：
1. 一鍵拉取 Polymarket 鏈上真金白銀預測勝率 與 Sportsbet 即時賠率。
2. 扣除抽水 (Devigging) 萃取真實客觀勝率與公平賠率 (Fair Odds)。
3. 智能比對賽事與隊伍，計算每一盤口的期望值 (EV%) 與邊際優勢 (Edge%)。
4. 標記正期望值 (+EV) 之「金礦」項目，並依 1/4 凱利公式給出風控下注建議。
5. 支援輸出 Rich 終端報表、Telegram Markdown 或 JSON。
-----------------------------------------------------------------------------
"""

import sys
import json
import argparse
import time
from typing import List, Dict, Optional

try:
    from .polymarket_client import PolymarketClient
    from .devig_engine import DevigEngine
    from .sports_matcher import SportsMatcher
    from .query_sportsbet import fetch_sportsbet_matches
    from .proxy_config import get_active_proxy, load_agent_config
except ImportError:
    from polymarket_client import PolymarketClient
    from devig_engine import DevigEngine
    from sports_matcher import SportsMatcher
    from query_sportsbet import fetch_sportsbet_matches
    from proxy_config import get_active_proxy, load_agent_config


class MarketComparator:
    def __init__(self, proxy_server: Optional[str] = "__AUTO__"):
        resolved_proxy = get_active_proxy() if proxy_server == "__AUTO__" else proxy_server
        self.pm_client = PolymarketClient(proxy_server=resolved_proxy)

    def compare_sport_markets(
        self,
        sport_query: str = "nba",
        min_ev_pct: float = -50.0,
        bankroll: float = 100.0,
        max_stake_limit: float = 20.0,
        kelly_fraction: float = 0.25,
    ) -> Dict:
        """
        比對指定球種在 Sportsbet 與 Polymarket 的盤口 (Read-Only)
        :param sport_query: 球種關鍵字 (nba, lol, soccer 等)
        :param min_ev_pct: 最低顯示 EV% 門檻 (預設顯示所有比對結果)
        """
        start_time = time.time()
        print(f"🚀 開始跨平台盤口比對作業 [目標項目: {sport_query.upper()}]...")

        # 1. 抓取 Sportsbet 盤口
        print(f"📡 [1/2] 正在自 Sportsbet 澳洲伺服器抓取即時盤口...")
        sb_matches, route_info = fetch_sportsbet_matches(sport_query)
        print(f"   • Sportsbet 已獲取 {len(sb_matches)} 場賽事。")

        # 2. 抓取 Polymarket 盤口
        print(f"🌐 [2/2] 正在自 Polymarket 鏈上預測市場抓取對照賽事...")
        pm_matches = self.pm_client.fetch_all_sports_matchups(sport_filter=sport_query)
        print(f"   • Polymarket 已獲取 {len(pm_matches)} 場活躍單場賽事。")

        # 3. 跨市場實體對齊與量化計算
        print("⚙️ [3/3] 正在進行實體隊伍對齊、去水 (Devigging) 與 EV 計算...")
        aligned_results = []
        gold_mines_count = 0

        for sb_m in sb_matches:
            sb_team1 = sb_m.get("team1")
            sb_team2 = sb_m.get("team2")
            if not sb_team1 or not sb_team2:
                continue

            sb_odds_list = sb_m.get("odds", [])
            if len(sb_odds_list) < 2:
                continue

            try:
                sb_odd1 = float(sb_odds_list[0]["val"])
                sb_odd2 = float(sb_odds_list[-1]["val"])
            except (ValueError, TypeError):
                continue

            # 尋找 Polymarket 對應賽事
            matched_pm = None
            align_indices = None

            for pm_m in pm_matches:
                ml = pm_m.get("moneyline")
                if not ml:
                    continue
                pm_outcomes = ml.get("outcomes", [])
                if len(pm_outcomes) < 2:
                    continue

                res = SportsMatcher.match_two_way_game(
                    sb_team1, sb_team2,
                    pm_outcomes[0], pm_outcomes[1]
                )
                if res:
                    matched_pm = pm_m
                    align_indices = res
                    break

            if not matched_pm or not align_indices:
                continue

            pm_ml = matched_pm["moneyline"]
            pm_outcomes = pm_ml["outcomes"]
            pm_raw_prices = pm_ml["prices"]

            if len(pm_raw_prices) < 2:
                continue

            # 4. 去水計算 (Devigging)
            devigged = DevigEngine.devig_proportional([pm_raw_prices[0], pm_raw_prices[1]])
            pm_true_probs = devigged["true_probabilities"]
            pm_fair_odds = devigged["fair_odds"]

            # 依據對齊索引將 Polymarket 的去水機率對應給 Sportsbet 隊伍
            idx_sb1_in_pm = align_indices[0]
            idx_sb2_in_pm = align_indices[1]

            true_prob_sb1 = pm_true_probs[idx_sb1_in_pm]
            true_prob_sb2 = pm_true_probs[idx_sb2_in_pm]
            fair_odd_sb1 = pm_fair_odds[idx_sb1_in_pm]
            fair_odd_sb2 = pm_fair_odds[idx_sb2_in_pm]

            # 5. EV 期望值與凱利分析
            analysis_team1 = DevigEngine.analyze_bet_opportunity(
                sb_team1, true_prob_sb1, sb_odd1,
                bankroll=bankroll, max_stake_limit=max_stake_limit, kelly_fraction=kelly_fraction
            )
            analysis_team2 = DevigEngine.analyze_bet_opportunity(
                sb_team2, true_prob_sb2, sb_odd2,
                bankroll=bankroll, max_stake_limit=max_stake_limit, kelly_fraction=kelly_fraction
            )

            has_gold = analysis_team1["is_positive_ev"] or analysis_team2["is_positive_ev"]
            if has_gold:
                gold_mines_count += 1

            # 只要有一隊符合最低 EV 門檻即收錄
            if analysis_team1["ev_pct"] >= min_ev_pct or analysis_team2["ev_pct"] >= min_ev_pct:
                aligned_results.append({
                    "matchup": sb_m["matchup"],
                    "time": sb_m.get("time", ""),
                    "sport": route_info.get("name", sport_query),
                    "polymarket_slug": matched_pm["slug"],
                    "polymarket_vol_24h": matched_pm["volume_24h"],
                    "polymarket_vig_pct": devigged["vig_pct"],
                    "team1_analysis": analysis_team1,
                    "team2_analysis": analysis_team2,
                    "has_gold_mine": has_gold
                })

        # 依照最高 EV% 排序
        aligned_results.sort(
            key=lambda x: max(x["team1_analysis"]["ev_pct"], x["team2_analysis"]["ev_pct"]),
            reverse=True
        )

        elapsed = round(time.time() - start_time, 2)
        return {
            "query": sport_query,
            "elapsed_seconds": elapsed,
            "total_sportsbet_matches": len(sb_matches),
            "total_polymarket_games": len(pm_matches),
            "matched_games_count": len(aligned_results),
            "gold_mines_count": gold_mines_count,
            "results": aligned_results
        }


def format_cli_report(data: Dict) -> str:
    """產出終端 / Telegram 格式化精美對比報告"""
    results = data.get("results", [])
    q = data.get("query", "").upper()
    total_matched = data.get("matched_games_count", 0)
    golds = data.get("gold_mines_count", 0)
    elapsed = data.get("elapsed_seconds", 0)

    header = [
        "=" * 72,
        f"🏆 Sportsbet vs Polymarket 跨市場量化對比報告 ｜ 項目：{q}",
        f"⏱️ 耗時：{elapsed}s ｜ 成功對齊：{total_matched} 場 ｜ 發現金礦：{golds} 項",
        "=" * 72,
        ""
    ]

    if not results:
        header.append("⚠️ 目前尚未比對到跨平台同時開盤之相符賽事。請確認兩邊賽事開盤排程。")
        return "\n".join(header)

    lines = list(header)
    for i, item in enumerate(results, 1):
        mup = item["matchup"]
        t1 = item["team1_analysis"]
        t2 = item["team2_analysis"]
        pm_vol = item["polymarket_vol_24h"]
        slug = item["polymarket_slug"]

        is_gold = item["has_gold_mine"]
        gold_badge = "🌟【發現金礦 +EV】" if is_gold else "⚖️【定價均衡 / 莊家抽水】"

        lines.append(f"<b>{i}. {mup}</b>  {gold_badge}")
        lines.append(f"   • 開賽時間：<code>{item['time']}</code> ｜ Polymarket 24h 量：<code>${pm_vol:,.0f} USD</code>")

        # Team 1
        t1_ev = t1["ev_pct"]
        t1_gold = "🔥 金礦" if t1["is_positive_ev"] else ""
        lines.append(
            f"   ▸ <b>{t1['selection']}</b>：Sportsbet 賠率 <code>{t1['offered_odds']}</code> "
            f"| 標竿真勝率 <code>{t1['true_win_rate_pct']}%</code> (公平賠率 {t1['fair_odds']}) "
            f"| EV: <b>{t1_ev:+}%</b> {t1_gold}"
        )
        if t1["is_positive_ev"]:
            lines.append(f"     👉 建議投注額 (1/4 凱利)：<code>${t1['recommended_stake']} AUD</code>")

        # Team 2
        t2_ev = t2["ev_pct"]
        t2_gold = "🔥 金礦" if t2["is_positive_ev"] else ""
        lines.append(
            f"   ▸ <b>{t2['selection']}</b>：Sportsbet 賠率 <code>{t2['offered_odds']}</code> "
            f"| 標竿真勝率 <code>{t2['true_win_rate_pct']}%</code> (公平賠率 {t2['fair_odds']}) "
            f"| EV: <b>{t2_ev:+}%</b> {t2_gold}"
        )
        if t2["is_positive_ev"]:
            lines.append(f"     👉 建議投注額 (1/4 凱利)：<code>${t2['recommended_stake']} AUD</code>")

        lines.append(f"   🔗 Polymarket: <code>{slug}</code>\n")

    lines.append("=" * 72)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Sportsbet vs Polymarket 量化比價器")
    parser.add_argument("--sport", default="nba", help="運動類別 (nba, lol, soccer, mlb 等)")
    parser.add_argument("--min-ev", type=float, default=-50.0, help="最低顯示 EV 百分比門檻")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式輸出")

    args = parser.parse_args()

    comparator = MarketComparator()
    data = comparator.compare_sport_markets(sport_query=args.sport, min_ev_pct=args.min_ev)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_cli_report(data))


if __name__ == "__main__":
    main()

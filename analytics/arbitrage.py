"""
跨平台套利空間計算模組 (Cross-Market Arbitrage & Surebet Calculator)
比對 Sportsbet 與 Oddsportal 市場共識/國際盤口，計算無風險套利報酬與最適注碼分配
"""
import pandas as pd
from typing import List, Dict, Any, Optional
from database.db_manager import db

class ArbitrageScanner:
    def scan_arbitrage_opportunities(self, total_bankroll: float = 1000.0) -> List[Dict[str, Any]]:
        """
        掃描所有即時賽事的跨平台無風險套利機會
        比對:
          組合 1: Sportsbet 押主隊 vs Oddsportal 押客隊
          組合 2: Sportsbet 押客隊 vs Oddsportal 押主隊
        """
        opportunities = []
        df = db.get_live_matches_with_odds()
        if df.empty:
            return opportunities

        for _, row in df.iterrows():
            sb_h = float(row["sb_home_odds"] or 0)
            sb_a = float(row["sb_away_odds"] or 0)
            op_h = float(row["op_home_odds"] or 0)
            op_a = float(row["op_away_odds"] or 0)

            # 1. 獨贏盤套利 (Moneyline Arbitrage)
            # 方案 A: Sportsbet 買主隊 (sb_h), 市場共識買客隊 (op_a)
            if sb_h > 1.0 and op_a > 1.0:
                inv_sum_a = (1.0 / sb_h) + (1.0 / op_a)
                if inv_sum_a < 1.0: # 套利存在！
                    roi_a = round(((1.0 / inv_sum_a) - 1.0) * 100, 2)
                    stake_sb = round((total_bankroll * (1.0 / sb_h)) / inv_sum_a, 2)
                    stake_op = round(total_bankroll - stake_sb, 2)
                    guaranteed_payout = round(stake_sb * sb_h, 2)
                    net_profit = round(guaranteed_payout - total_bankroll, 2)

                    opportunities.append({
                        "match_id": row["match_id"],
                        "league": row["league"],
                        "home_team": row["home_team"],
                        "away_team": row["away_team"],
                        "market": "獨贏 (ML)",
                        "side_a": f"Sportsbet: {row['home_team']} @ {sb_h}",
                        "side_b": f"市場對手盤: {row['away_team']} @ {op_a}",
                        "arb_margin": round(inv_sum_a, 4),
                        "roi_pct": roi_a,
                        "stake_a": f"${stake_sb} (Sportsbet)",
                        "stake_b": f"${stake_op} (市場對沖)",
                        "net_profit": f"+${net_profit} (保證獲利)",
                        "rating": "⚡ 無風險套利"
                    })

            # 方案 B: Sportsbet 買客隊 (sb_a), 市場共識買主隊 (op_h)
            if sb_a > 1.0 and op_h > 1.0:
                inv_sum_b = (1.0 / sb_a) + (1.0 / op_h)
                if inv_sum_b < 1.0:
                    roi_b = round(((1.0 / inv_sum_b) - 1.0) * 100, 2)
                    stake_sb = round((total_bankroll * (1.0 / sb_a)) / inv_sum_b, 2)
                    stake_op = round(total_bankroll - stake_sb, 2)
                    guaranteed_payout = round(stake_sb * sb_a, 2)
                    net_profit = round(guaranteed_payout - total_bankroll, 2)

                    opportunities.append({
                        "match_id": row["match_id"],
                        "league": row["league"],
                        "home_team": row["home_team"],
                        "away_team": row["away_team"],
                        "market": "獨贏 (ML)",
                        "side_a": f"Sportsbet: {row['away_team']} @ {sb_a}",
                        "side_b": f"市場對手盤: {row['home_team']} @ {op_h}",
                        "arb_margin": round(inv_sum_b, 4),
                        "roi_pct": roi_b,
                        "stake_a": f"${stake_sb} (Sportsbet)",
                        "stake_b": f"${stake_op} (市場對沖)",
                        "net_profit": f"+${net_profit} (保證獲利)",
                        "rating": "⚡ 無風險套利"
                    })

        return opportunities

arbitrage_scanner = ArbitrageScanner()

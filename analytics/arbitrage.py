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
        掃描所有即時賽事的 4 大來源 (Sportsbet, Polymarket, Kalshi, Oddsportal) 跨平台無風險套利機會
        """
        opportunities = []
        df = db.get_live_matches_with_odds()
        if df.empty:
            return opportunities

        source_pairs = [
            ("Sportsbet", "sb_home_odds", "sb_away_odds", "🇦🇺 Sportsbet"),
            ("Polymarket", "poly_home_odds", "poly_away_odds", "🟣 Polymarket"),
            ("Kalshi", "kalshi_home_odds", "kalshi_away_odds", "🟢 Kalshi"),
            ("Oddsportal", "op_home_odds", "op_away_odds", "🌐 Oddsportal")
        ]

        for _, row in df.iterrows():
            # 遍歷所有兩兩平台組合 (A 買主隊, B 買客隊)
            for i, (name_a, col_h_a, col_a_a, disp_a) in enumerate(source_pairs):
                for j, (name_b, col_h_b, col_a_b, disp_b) in enumerate(source_pairs):
                    if i >= j:
                        continue # 避免重複或同平台比較

                    odds_h_a = float(row.get(col_h_a) or 0)
                    odds_a_b = float(row.get(col_a_b) or 0)
                    odds_h_b = float(row.get(col_h_b) or 0)
                    odds_a_a = float(row.get(col_a_a) or 0)

                    # 方案 1: A 平台買主隊, B 平台買客隊
                    if odds_h_a > 1.0 and odds_a_b > 1.0:
                        inv_sum_1 = (1.0 / odds_h_a) + (1.0 / odds_a_b)
                        if inv_sum_1 < 1.0: # 套利成立
                            roi_1 = round(((1.0 / inv_sum_1) - 1.0) * 100, 2)
                            stake_1 = round((total_bankroll * (1.0 / odds_h_a)) / inv_sum_1, 2)
                            stake_2 = round(total_bankroll - stake_1, 2)
                            guaranteed_payout = round(stake_1 * odds_h_a, 2)
                            net_profit = round(guaranteed_payout - total_bankroll, 2)

                            opportunities.append({
                                "match_id": row["match_id"],
                                "league": row["league"],
                                "home_team": row["home_team"],
                                "away_team": row["away_team"],
                                "market": "獨贏 (ML)",
                                "pair": f"{disp_a} vs {disp_b}",
                                "side_a": f"{disp_a}: {row['home_team']} (主) @ {odds_h_a}",
                                "side_b": f"{disp_b}: {row['away_team']} (客) @ {odds_a_b}",
                                "arb_margin": round(inv_sum_1, 4),
                                "roi_pct": roi_1,
                                "stake_a": f"${stake_1} ({disp_a})",
                                "stake_b": f"${stake_2} ({disp_b})",
                                "net_profit": f"+${net_profit} (保證獲利)",
                                "rating": "⚡ 無風險套利"
                            })

                    # 方案 2: B 平台買主隊, A 平台買客隊
                    if odds_h_b > 1.0 and odds_a_a > 1.0:
                        inv_sum_2 = (1.0 / odds_h_b) + (1.0 / odds_a_a)
                        if inv_sum_2 < 1.0: # 套利成立
                            roi_2 = round(((1.0 / inv_sum_2) - 1.0) * 100, 2)
                            stake_1 = round((total_bankroll * (1.0 / odds_h_b)) / inv_sum_2, 2)
                            stake_2 = round(total_bankroll - stake_1, 2)
                            guaranteed_payout = round(stake_1 * odds_h_b, 2)
                            net_profit = round(guaranteed_payout - total_bankroll, 2)

                            opportunities.append({
                                "match_id": row["match_id"],
                                "league": row["league"],
                                "home_team": row["home_team"],
                                "away_team": row["away_team"],
                                "market": "獨贏 (ML)",
                                "pair": f"{disp_b} vs {disp_a}",
                                "side_a": f"{disp_b}: {row['home_team']} (主) @ {odds_h_b}",
                                "side_b": f"{disp_a}: {row['away_team']} (客) @ {odds_a_a}",
                                "arb_margin": round(inv_sum_2, 4),
                                "roi_pct": roi_2,
                                "stake_a": f"${stake_1} ({disp_b})",
                                "stake_b": f"${stake_2} ({disp_a})",
                                "net_profit": f"+${net_profit} (保證獲利)",
                                "rating": "⚡ 無風險套利"
                            })

        # 依 ROI 由高到低排序
        opportunities.sort(key=lambda x: x["roi_pct"], reverse=True)
        return opportunities

arbitrage_scanner = ArbitrageScanner()


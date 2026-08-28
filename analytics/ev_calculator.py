"""
期望值 (+EV) 與隱含勝率預測模組 (Expected Value & True Probability Engine)
去除抽水 (De-vigging) 算出真實勝率，並透過 Kelly 準則給予科學投注建議
"""
import pandas as pd
from typing import List, Dict, Any, Optional
from database.db_manager import db

class EVCalculator:
    @staticmethod
    def remove_vig_proportional(odds_1: float, odds_2: float) -> tuple[float, float]:
        """去除博彩公司抽水 (Overround Removal)，計算公正真實勝率"""
        if odds_1 <= 0 or odds_2 <= 0:
            return 0.5, 0.5
        implied_1 = 1.0 / odds_1
        implied_2 = 1.0 / odds_2
        total_implied = implied_1 + implied_2
        true_p1 = implied_1 / total_implied
        true_p2 = implied_2 / total_implied
        return true_p1, true_p2

    def scan_positive_ev(self, min_ev_pct: float = 0.0, kelly_fraction: float = 0.25) -> List[Dict[str, Any]]:
        """
        掃描 4 大來源 (Sportsbet, Polymarket, Kalshi) 盤口中具有正期望值 (+EV) 的價值投注
        利用 Oddsportal 及跨預測市場平均作為公正真實勝率基準
        """
        ev_bets = []
        df = db.get_live_matches_with_odds()
        if df.empty:
            return ev_bets

        sources_to_check = [
            ("Sportsbet", "sb_home_odds", "sb_away_odds", "🇦🇺 Sportsbet"),
            ("Polymarket", "poly_home_odds", "poly_away_odds", "🟣 Polymarket"),
            ("Kalshi", "kalshi_home_odds", "kalshi_away_odds", "🟢 Kalshi")
        ]

        for _, row in df.iterrows():
            op_h = float(row.get("op_home_odds") or 0)
            op_a = float(row.get("op_away_odds") or 0)

            # 基準真勝率
            if op_h <= 1.0 or op_a <= 1.0:
                # 備用 Polymarket/Sportsbet 平均
                sb_h = float(row.get("sb_home_odds") or 1.9)
                sb_a = float(row.get("sb_away_odds") or 1.9)
                true_p_h, true_p_a = self.remove_vig_proportional(sb_h, sb_a)
            else:
                true_p_h, true_p_a = self.remove_vig_proportional(op_h, op_a)

            for s_name, col_h, col_a, disp_name in sources_to_check:
                s_h = float(row.get(col_h) or 0)
                s_a = float(row.get(col_a) or 0)

                # 檢驗主隊是否為 +EV
                if s_h > 1.0:
                    ev_h = (true_p_h * s_h) - 1.0
                    if (ev_h * 100.0) >= min_ev_pct:
                        b = s_h - 1.0
                        full_kelly = ((true_p_h * b) - (1.0 - true_p_h)) / b if b > 0 else 0.0
                        suggested_kelly = max(0.0, full_kelly * kelly_fraction) * 100.0
                        ev_bets.append({
                            "match_id": row["match_id"],
                            "league": row["league"],
                            "source": disp_name,
                            "team": row["home_team"],
                            "side": "主隊 (Home)",
                            "opponent": row["away_team"],
                            "odds": s_h,
                            "fair_odds": round(1.0 / true_p_h, 2) if true_p_h > 0 else 2.0,
                            "true_win_rate": f"{round(true_p_h * 100, 1)}%",
                            "ev_pct": round(ev_h * 100, 2),
                            "kelly_stake_pct": f"{round(suggested_kelly, 1)}%",
                            "rating": "🔥 高價值投注 (+EV)" if (ev_h * 100) >= 3.5 else "✅ 價值投注 (+EV)"
                        })

                # 檢驗客隊是否為 +EV
                if s_a > 1.0:
                    ev_a = (true_p_a * s_a) - 1.0
                    if (ev_a * 100.0) >= min_ev_pct:
                        b = s_a - 1.0
                        full_kelly = ((true_p_a * b) - (1.0 - true_p_a)) / b if b > 0 else 0.0
                        suggested_kelly = max(0.0, full_kelly * kelly_fraction) * 100.0
                        ev_bets.append({
                            "match_id": row["match_id"],
                            "league": row["league"],
                            "source": disp_name,
                            "team": row["away_team"],
                            "side": "客隊 (Away)",
                            "opponent": row["home_team"],
                            "odds": s_a,
                            "fair_odds": round(1.0 / true_p_a, 2) if true_p_a > 0 else 2.0,
                            "true_win_rate": f"{round(true_p_a * 100, 1)}%",
                            "ev_pct": round(ev_a * 100, 2),
                            "kelly_stake_pct": f"{round(suggested_kelly, 1)}%",
                            "rating": "🔥 高價值投注 (+EV)" if (ev_a * 100) >= 3.5 else "✅ 價值投注 (+EV)"
                        })

        # 依 EV% 降序排列
        ev_bets.sort(key=lambda x: x["ev_pct"], reverse=True)
        return ev_bets

ev_calculator = EVCalculator()


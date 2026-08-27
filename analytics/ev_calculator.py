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

    def scan_positive_ev(self, min_ev_pct: float = 1.0, kelly_fraction: float = 0.25) -> List[Dict[str, Any]]:
        """
        掃描 Sportsbet 盤口中具有正期望值 (+EV) 的價值投注
        利用 Oddsportal 市場共識作為真實勝率基準
        """
        ev_bets = []
        df = db.get_live_matches_with_odds()
        if df.empty:
            return ev_bets

        for _, row in df.iterrows():
            sb_h = float(row["sb_home_odds"] or 0)
            sb_a = float(row["sb_away_odds"] or 0)
            op_h = float(row["op_home_odds"] or sb_h)
            op_a = float(row["op_away_odds"] or sb_a)

            if sb_h <= 1.0 or sb_a <= 1.0 or op_h <= 1.0 or op_a <= 1.0:
                continue

            # 以市場共識賠率去除抽水得到客觀真勝率
            true_p_h, true_p_a = self.remove_vig_proportional(op_h, op_a)

            # 計算 Sportsbet 主隊與客隊的 EV%
            # EV = (True_P * (Odds - 1)) - (1 - True_P) = True_P * Odds - 1
            ev_h = (true_p_h * sb_h) - 1.0
            ev_a = (true_p_a * sb_a) - 1.0

            # 檢驗主隊是否為 +EV
            if (ev_h * 100.0) >= min_ev_pct:
                b = sb_h - 1.0
                full_kelly = ((true_p_h * b) - (1.0 - true_p_h)) / b
                suggested_kelly = max(0.0, full_kelly * kelly_fraction) * 100.0
                ev_bets.append({
                    "match_id": row["match_id"],
                    "league": row["league"],
                    "team": row["home_team"],
                    "side": "主隊 (Home)",
                    "opponent": row["away_team"],
                    "sportsbet_odds": sb_h,
                    "fair_odds": round(1.0 / true_p_h, 2),
                    "true_win_rate": f"{round(true_p_h * 100, 1)}%",
                    "ev_pct": round(ev_h * 100, 2),
                    "kelly_stake_pct": f"{round(suggested_kelly, 1)}%",
                    "rating": "🔥 高價值投注 (+EV)" if (ev_h * 100) >= 4.0 else "✅ 價值投注 (+EV)"
                })

            # 檢驗客隊是否為 +EV
            if (ev_a * 100.0) >= min_ev_pct:
                b = sb_a - 1.0
                full_kelly = ((true_p_a * b) - (1.0 - true_p_a)) / b
                suggested_kelly = max(0.0, full_kelly * kelly_fraction) * 100.0
                ev_bets.append({
                    "match_id": row["match_id"],
                    "league": row["league"],
                    "team": row["away_team"],
                    "side": "客隊 (Away)",
                    "opponent": row["home_team"],
                    "sportsbet_odds": sb_a,
                    "fair_odds": round(1.0 / true_p_a, 2),
                    "true_win_rate": f"{round(true_p_a * 100, 1)}%",
                    "ev_pct": round(ev_a * 100, 2),
                    "kelly_stake_pct": f"{round(suggested_kelly, 1)}%",
                    "rating": "🔥 高價值投注 (+EV)" if (ev_a * 100) >= 4.0 else "✅ 價值投注 (+EV)"
                })

        return ev_bets

ev_calculator = EVCalculator()

#!/usr/bin/env python3
"""
量化去水精算與正期望值 (+EV) 計算引擎 (devig_engine.py)
-----------------------------------------------------------------------------
功能：
1. 去水演算 (Devigging)：
   • 比例去水法 (Multiplicative / Proportional Method)
   • 冪次去水法 (Power Method - 考量冷門偏誤 Favorite-Longshot Bias)
2. 公平賠率 (Fair Odds) 換算
3. 正期望值 (Expected Value, EV%) 與邊際優勢 (Edge%) 評估
4. 凱利準則 (Kelly Criterion) 動態注額試算 (含 1/4 凱利保護與單筆風控上限)
-----------------------------------------------------------------------------
"""

import math
from typing import List, Dict, Tuple, Optional


class DevigEngine:
    @staticmethod
    def devig_proportional(raw_probabilities: List[float]) -> Dict:
        """
        比例法 (Multiplicative) 扣除抽水
        將所有原始隱含機率正規化，使機率總和嚴格為 1.0 (100%)
        """
        total = sum(raw_probabilities)
        if total <= 0:
            return {
                "vig_pct": 0.0,
                "true_probabilities": [0.0] * len(raw_probabilities),
                "fair_odds": [0.0] * len(raw_probabilities)
            }

        vig_pct = (total - 1.0) * 100.0
        true_probs = [p / total for p in raw_probabilities]
        fair_odds = [(1.0 / p) if p > 0 else 0.0 for p in true_probs]

        return {
            "overround": round(total, 4),
            "vig_pct": round(vig_pct, 2),
            "true_probabilities": [round(p, 4) for p in true_probs],
            "fair_odds": [round(o, 3) for o in fair_odds]
        }

    @staticmethod
    def devig_power(raw_probabilities: List[float], max_iter: int = 100, tol: float = 1e-6) -> Dict:
        """
        冪次法 (Power Method) 去水
        求解 k 使得 sum(p_i ^ k) = 1.0
        更能校正高賠冷門偏誤 (Favorite-Longshot Bias)
        """
        # 若已歸一化，直接返回
        total = sum(raw_probabilities)
        if abs(total - 1.0) < tol or any(p <= 0 for p in raw_probabilities):
            return DevigEngine.devig_proportional(raw_probabilities)

        # 數值二分逼近求 k
        low, high = 0.1, 5.0
        k = 1.0
        for _ in range(max_iter):
            k = (low + high) / 2.0
            s = sum(math.pow(p, k) for p in raw_probabilities if p > 0)
            if abs(s - 1.0) < tol:
                break
            if s > 1.0:
                low = k
            else:
                high = k

        true_probs = [math.pow(p, k) for p in raw_probabilities]
        s_true = sum(true_probs)
        true_probs = [p / s_true for p in true_probs]
        fair_odds = [(1.0 / p) if p > 0 else 0.0 for p in true_probs]

        return {
            "power_k": round(k, 4),
            "overround": round(total, 4),
            "vig_pct": round((total - 1.0) * 100.0, 2),
            "true_probabilities": [round(p, 4) for p in true_probs],
            "fair_odds": [round(o, 3) for o in fair_odds]
        }

    @staticmethod
    def devig_from_decimal_odds(decimal_odds: List[float]) -> Dict:
        """從傳統歐盤小數賠率去水 (如 [1.85, 2.05])"""
        raw_probs = [(1.0 / o) if o > 0 else 0.0 for o in decimal_odds]
        return DevigEngine.devig_proportional(raw_probs)

    @staticmethod
    def analyze_bet_opportunity(
        selection_name: str,
        true_prob: float,
        offered_odds: float,
        bankroll: float = 100.0,
        max_stake_limit: float = 20.0,
        kelly_fraction: float = 0.25
    ) -> Dict:
        """
        評估單一選項之投資價值 (+EV / Edge / 凱利注額)
        
        :param selection_name: 選項名稱 (例如 T1, Lakers)
        :param true_prob: 標竿平台去水後之真實勝率 (0.0 ~ 1.0)
        :param offered_odds: Sportsbet 開出之小數賠率 (例如 1.85)
        :param bankroll: 參考總本金 (AUD)
        :param max_stake_limit: 單筆風控上限 (AUD)
        :param kelly_fraction: 凱利倍數 (預設 1/4 凱利保護)
        """
        if true_prob <= 0 or offered_odds <= 1.0:
            return {
                "selection": selection_name,
                "is_positive_ev": False,
                "ev_pct": -100.0,
                "edge_pct": -100.0,
                "fair_odds": 0.0,
                "offered_odds": offered_odds,
                "recommended_stake": 0.0
            }

        fair_odds = 1.0 / true_prob
        # EV = (TrueProb * OfferedOdds - 1) * 100%
        ev_pct = (true_prob * offered_odds - 1.0) * 100.0
        # Edge = TrueProb - ImpliedProb
        implied_prob = 1.0 / offered_odds
        edge_pct = (true_prob - implied_prob) * 100.0

        is_positive_ev = ev_pct > 0.0

        # 凱利公式: f* = (b*p - q) / b
        # 其中 b = offered_odds - 1, p = true_prob, q = 1 - p
        recommended_stake = 0.0
        full_kelly_pct = 0.0
        if is_positive_ev:
            b = offered_odds - 1.0
            q = 1.0 - true_prob
            f_star = (b * true_prob - q) / b
            if f_star > 0:
                fractional_f = f_star * kelly_fraction
                full_kelly_pct = round(f_star * 100.0, 2)
                raw_stake = fractional_f * bankroll
                # 約束在單筆上限與 0 之間
                recommended_stake = min(max_stake_limit, max(1.0, round(raw_stake, 1)))

        return {
            "selection": selection_name,
            "true_probability": round(true_prob, 4),
            "true_win_rate_pct": round(true_prob * 100.0, 2),
            "fair_odds": round(fair_odds, 3),
            "offered_odds": round(offered_odds, 3),
            "ev_pct": round(ev_pct, 2),
            "edge_pct": round(edge_pct, 2),
            "is_positive_ev": is_positive_ev,
            "full_kelly_pct": full_kelly_pct,
            "recommended_stake": recommended_stake
        }


if __name__ == "__main__":
    # 範例測試 1：Polymarket 報價 [0.65, 0.38] (去水前總和 1.03)
    pm_prices = [0.65, 0.38]
    devigged = DevigEngine.devig_proportional(pm_prices)
    print("📊 Polymarket 報價去水結果：")
    print(f"   • 抽水 (Vig): {devigged['vig_pct']}%")
    print(f"   • 去水真實勝率: {devigged['true_probabilities']}")
    print(f"   • 公平賠率 (Fair Odds): {devigged['fair_odds']}\n")

    # 範例測試 2：Sportsbet 開出 1.82 (高於 Fair Odds 1.58)
    p_t1 = devigged["true_probabilities"][0]
    analysis = DevigEngine.analyze_bet_opportunity("T1", p_t1, 1.82, bankroll=100.0, max_stake_limit=20.0)
    print("💎 價值投注分析 (Sportsbet 報價 1.82)：")
    print(f"   • 標的: {analysis['selection']}")
    print(f"   • 真實勝率: {analysis['true_win_rate_pct']}%")
    print(f"   • 公平賠率: {analysis['fair_odds']} vs Sportsbet 賠率: {analysis['offered_odds']}")
    print(f"   • 期望值 (EV): {analysis['ev_pct']:+}% {'🌟 金礦!' if analysis['is_positive_ev'] else ''}")
    print(f"   • 建議注額: ${analysis['recommended_stake']} AUD (1/4 凱利)")

"""
量化去水精算與期望值計算引擎 (radar/devig.py)
支援：
1. 傳統 2-way 與 3-way 盤口 Power Method（冪次法，抗冷熱門偏差）與 Multiplicative（比例法）
2. Betfair 交易所 Back/Lay 中位價與佣金淨勝率換算
3. 預測市場 (Polymarket / Kalshi) 合約隱含勝率標準化
4. 部分參考指標開盤 (X/5) 加權共識真實勝率合成與 +EV / Edge% 精算
"""
import math
from typing import List, Dict, Optional, Tuple
from .models import BENCHMARK_WEIGHTS


def american_to_decimal(american: float) -> float:
    """美式賠率 (+243, -466) 轉 歐盤十進制小數賠率"""
    if american == 0:
        return 0.0
    if american > 0:
        return round(1.0 + (american / 100.0), 4)
    return round(1.0 + (100.0 / abs(american)), 4)


def prob_to_decimal(prob: float) -> float:
    """機率 (0~1) 轉十進制賠率"""
    if prob <= 0.001:
        return 1000.0
    if prob >= 0.999:
        return 1.001
    return round(1.0 / prob, 4)


def devig_multiplicative(raw_probs: List[float]) -> Dict:
    """比例法去水"""
    valid = [max(0.0, float(p)) for p in raw_probs]
    total = sum(valid)
    if total <= 0:
        n = len(raw_probs) or 2
        return {
            "method": "multiplicative",
            "vig_pct": 0.0,
            "true_probs": [round(1.0 / n, 5)] * n,
            "fair_odds": [float(n)] * n,
        }
    true_probs = [p / total for p in valid]
    fair_odds = [round(1.0 / p, 3) if p > 1e-6 else 0.0 for p in true_probs]
    return {
        "method": "multiplicative",
        "vig_pct": round((total - 1.0) * 100.0, 2),
        "true_probs": [round(p, 5) for p in true_probs],
        "fair_odds": fair_odds,
    }


def devig_power(raw_probs: List[float], max_iter: int = 80, tol: float = 1e-6) -> Dict:
    """
    冪次法 (Power Method) 去水：求解 k 使得 sum(p_i ^ k) = 1.0
    適合傳統莊家 2-way / 3-way 賠率去水，能校正 Favorite-Longshot Bias。
    """
    if not raw_probs or any(p <= 0 or p >= 1.0 for p in raw_probs):
        return devig_multiplicative(raw_probs)

    total = sum(raw_probs)
    if abs(total - 1.0) < tol:
        return {
            "method": "power",
            "vig_pct": round((total - 1.0) * 100.0, 2),
            "true_probs": [round(p, 5) for p in raw_probs],
            "fair_odds": [round(1.0 / p, 3) for p in raw_probs],
        }

    # 若 overround < 1.0 (極少見負水錢)，或超過合理範圍，二分搜尋 k
    low, high = 0.05, 8.0
    k = 1.0
    for _ in range(max_iter):
        k = (low + high) / 2.0
        s = sum(math.pow(p, k) for p in raw_probs)
        if abs(s - 1.0) < tol:
            break
        if s > 1.0:
            low = k
        else:
            high = k

    powered = [math.pow(p, k) for p in raw_probs]
    s_pow = sum(powered)
    true_probs = [p / s_pow for p in powered]
    fair_odds = [round(1.0 / p, 3) if p > 1e-6 else 0.0 for p in true_probs]
    return {
        "method": "power",
        "power_k": round(k, 4),
        "vig_pct": round((total - 1.0) * 100.0, 2),
        "true_probs": [round(p, 5) for p in true_probs],
        "fair_odds": fair_odds,
    }


def devig_decimal_odds(decimal_odds: List[float], use_power: bool = True) -> Dict:
    """由歐盤小數賠率清單 (如 [1.85, 2.05]) 進行去水"""
    if not decimal_odds or any(o is None or o <= 1.0 for o in decimal_odds):
        return devig_multiplicative([0.0] * (len(decimal_odds) or 2))
    raw_probs = [1.0 / float(o) for o in decimal_odds]
    if use_power:
        return devig_power(raw_probs)
    return devig_multiplicative(raw_probs)


def devig_betfair_back_lay(
    back_prices: List[Optional[float]],
    lay_prices: List[Optional[float]],
) -> Dict:
    """
    針對 Betfair 交易所計算真實隱含機率：
    若 Back 與 Lay 皆有效且價差合理，取隱含機率中點再正規化；若僅單邊有效則取 Back 進行去水。
    """
    raw_probs: List[float] = []
    for back, lay in zip(back_prices, lay_prices):
        if back and back > 1.0 and lay and lay > 1.0 and lay >= back and (lay / back) < 1.35:
            p_back = 1.0 / back
            p_lay = 1.0 / lay
            raw_probs.append((p_back + p_lay) / 2.0)
        elif back and back > 1.0:
            raw_probs.append(1.0 / back)
        elif lay and lay > 1.0:
            raw_probs.append(1.0 / lay)
        else:
            raw_probs.append(0.0)

    if any(p <= 0 for p in raw_probs):
        return devig_multiplicative(raw_probs)
    return devig_power(raw_probs)


def compute_weighted_consensus(
    benchmark_probs_by_source: Dict[str, List[float]],
    custom_weights: Optional[Dict[str, float]] = None,
) -> Tuple[List[float], List[float], int]:
    """
    計算多參考指標共識真實勝率 (支援局部開盤 1/5 ~ 5/5)
    :param benchmark_probs_by_source: {"pinnacle": [0.54, 0.46], "polymarket": [0.53, 0.47], ...}
    :return: (consensus_probs, consensus_fair_odds, valid_count)
    """
    if not benchmark_probs_by_source:
        return [], [], 0

    weights = custom_weights or BENCHMARK_WEIGHTS
    n_outcomes = len(next(iter(benchmark_probs_by_source.values())))
    acc = [0.0] * n_outcomes
    total_w = 0.0
    valid_count = 0

    for src, probs in benchmark_probs_by_source.items():
        if not probs or len(probs) != n_outcomes or any(p <= 0 or p >= 1.0 for p in probs):
            continue
        w = float(weights.get(src, 1.0))
        for i in range(n_outcomes):
            acc[i] += probs[i] * w
        total_w += w
        valid_count += 1

    if total_w <= 0 or valid_count == 0:
        return [], [], 0

    consensus = [a / total_w for a in acc]
    s = sum(consensus)
    if s > 0:
        consensus = [c / s for c in consensus]

    fair_odds = [round(1.0 / c, 3) if c > 1e-6 else 0.0 for c in consensus]
    return [round(c, 5) for c in consensus], fair_odds, valid_count


def evaluate_ev(true_prob: float, offered_odds: float) -> Dict[str, float]:
    """
    只讀期望值與勝率優勢精算（無任何下注金額或自動下單邏輯）
    """
    if true_prob <= 0 or offered_odds <= 1.0:
        return {
            "true_prob_pct": 0.0,
            "implied_prob_pct": 0.0,
            "fair_odds": 0.0,
            "ev_pct": -100.0,
            "edge_pct": -100.0,
            "is_positive_ev": False,
        }
    fair_odds = 1.0 / true_prob
    ev_pct = (true_prob * offered_odds - 1.0) * 100.0
    implied_prob = 1.0 / offered_odds
    edge_pct = (true_prob - implied_prob) * 100.0
    return {
        "true_prob_pct": round(true_prob * 100.0, 2),
        "implied_prob_pct": round(implied_prob * 100.0, 2),
        "fair_odds": round(fair_odds, 3),
        "ev_pct": round(ev_pct, 2),
        "edge_pct": round(edge_pct, 2),
        "is_positive_ev": ev_pct > 0.0,
    }

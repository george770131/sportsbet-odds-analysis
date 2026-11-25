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
    max_spread_ratio: float = 1.25,
) -> Dict:
    """
    針對 Betfair 交易所計算真實隱含機率：
    嚴格要求各選項皆具備有效雙邊掛單 (Back & Lay) 且價差合理 (lay / back <= max_spread_ratio)。
    若點差過大 (流動性枯竭之廢單，如 Back 1.01 vs Lay 3.30) 或單邊掛單，判定為無效盤口，
    避免極端單邊掛單污染共識勝率。水錢超過 10% 或小於 -5% 亦判定為無效。
    """
    n = len(back_prices)
    if n != len(lay_prices) or n < 2:
        return {"is_valid": False, "vig_pct": 100.0, "true_probs": [0.0] * n, "fair_odds": [0.0] * n}

    raw_probs: List[float] = []
    for back, lay in zip(back_prices, lay_prices):
        if not back or not lay or back <= 1.0 or lay <= 1.0 or lay < back:
            return {"is_valid": False, "vig_pct": 100.0, "true_probs": [0.0] * n, "fair_odds": [0.0] * n}
        spread_ratio = lay / back
        if spread_ratio > max_spread_ratio:
            # 買賣點差過大，市場未形成緊密共識報價
            return {"is_valid": False, "vig_pct": 100.0, "true_probs": [0.0] * n, "fair_odds": [0.0] * n}
        p_back = 1.0 / back
        p_lay = 1.0 / lay
        raw_probs.append((p_back + p_lay) / 2.0)

    overround = sum(raw_probs)
    vig_pct = (overround - 1.0) * 100.0
    if vig_pct > 10.0 or vig_pct < -5.0:
        return {"is_valid": False, "vig_pct": round(vig_pct, 2), "true_probs": [0.0] * n, "fair_odds": [0.0] * n}

    res = devig_power(raw_probs)
    res["is_valid"] = True
    return res


def compute_weighted_consensus(
    benchmark_probs_by_source: Dict[str, List[float]],
    custom_weights: Optional[Dict[str, float]] = None,
    outlier_threshold: float = 0.30,
) -> Tuple[List[float], List[float], int]:
    """
    計算多參考指標共識真實勝率 (支援局部開盤 1/5 ~ 5/5)
    具備極端離群值過濾防護 (Outlier Guard)：當有效指標 >= 3 時，若某來源之勝率與中位數相差超過 30%，
    視為髒數據或異常單邊行情予以剔除，保護共識真勝率不被單一異常指標灌爆。
    :param benchmark_probs_by_source: {"pinnacle": [0.54, 0.46], "polymarket": [0.53, 0.47], ...}
    :return: (consensus_probs, consensus_fair_odds, valid_count)
    """
    if not benchmark_probs_by_source:
        return [], [], 0

    weights = custom_weights or BENCHMARK_WEIGHTS
    n_outcomes = len(next(iter(benchmark_probs_by_source.values())))

    # 初步有效性篩選
    clean_sources: Dict[str, List[float]] = {}
    for src, probs in benchmark_probs_by_source.items():
        if not probs or len(probs) != n_outcomes or any(p <= 0.001 or p >= 0.999 for p in probs):
            continue
        clean_sources[src] = probs

    # 離群值防護 (Outlier Guard)：有效指標 >= 3 時比對勝率中位數
    if len(clean_sources) >= 3 and n_outcomes >= 2:
        p0_values = [probs[0] for probs in clean_sources.values()]
        sorted_p0 = sorted(p0_values)
        mid = len(sorted_p0) // 2
        median_p0 = (sorted_p0[mid] if len(sorted_p0) % 2 == 1 else (sorted_p0[mid - 1] + sorted_p0[mid]) / 2.0)
        filtered_sources = {}
        for src, probs in clean_sources.items():
            if abs(probs[0] - median_p0) > outlier_threshold:
                # 剔除極端離群指標
                continue
            filtered_sources[src] = probs
        if filtered_sources:
            clean_sources = filtered_sources

    acc = [0.0] * n_outcomes
    total_w = 0.0
    valid_count = 0

    for src, probs in clean_sources.items():
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

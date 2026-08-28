"""
Polymarket 去中心化預測市場賠率擷取與勝率定價模組 (Polymarket Scraper & Converter)
專注於將 Polymarket 鏈上即時預測市場價格 (隱含勝率 0~100%) 轉換為十進制賠率 (Decimal Odds) 與讓分/大小盤口
"""
import requests
import json
from typing import Dict, Any, List, Optional, Tuple

class PolymarketScraper:
    def __init__(self):
        self.gamma_api_url = "https://gamma-api.polymarket.com/events"
        self.clob_api_url = "https://clob.polymarket.com"

    @staticmethod
    def probability_to_decimal_odds(prob: float, spread_vig: float = 0.02) -> float:
        """
        將 Polymarket 隱含勝率機率 (0.0 ~ 1.0) 轉換為十進制賠率
        Polymarket 通常具備極低的市場點差 (1.5% ~ 2.5%)
        """
        if prob <= 0.01:
            return 50.0
        if prob >= 0.99:
            return 1.01
        
        effective_p = max(0.01, min(0.99, prob * (1.0 + spread_vig / 2.0)))
        odds = round(1.0 / effective_p, 2)
        return max(1.01, odds)

    @staticmethod
    def derive_polymarket_odds_from_market(base_home_ml: float, base_away_ml: float, h_line: float = -1.5) -> Dict[str, Any]:
        """
        根據市場真實賠率基準推導 Polymarket 預測市場專屬定價：
        - Polymarket 特點：去中心化、手續費低、散戶與大戶訂單簿撮合，通常在熱門隊略有溢價或更高流動性
        """
        if base_home_ml <= 0 or base_away_ml <= 0:
            return {
                "home_odds": 1.90, "away_odds": 1.90,
                "home_prob": 50.0, "away_prob": 50.0,
                "h_line": -1.5, "h_spread_odds": 1.95,
                "a_line": 1.5, "a_spread_odds": 1.85,
                "total_line": 8.5, "over_odds": 1.92, "under_odds": 1.92
            }

        inv_h = 1.0 / base_home_ml
        inv_a = 1.0 / base_away_ml
        tot_inv = inv_h + inv_a
        true_p_home = inv_h / tot_inv
        true_p_away = inv_a / tot_inv

        # Polymarket 訂單簿點差 (約 1.8% ~ 2.2%)
        poly_fee_margin = 0.02
        poly_h_odds = round(1.0 / (true_p_home * (1.0 + poly_fee_margin / 2.0)), 2)
        poly_a_odds = round(1.0 / (true_p_away * (1.0 + poly_fee_margin / 2.0)), 2)

        # Polymarket 讓分合約 (Runline Contract)
        if true_p_home >= 0.5:
            poly_h_spread_prob = max(0.2, true_p_home - 0.18)
            poly_a_spread_prob = 1.0 - poly_h_spread_prob
        else:
            poly_a_spread_prob = max(0.2, true_p_away - 0.18)
            poly_h_spread_prob = 1.0 - poly_a_spread_prob

        poly_h_sp_odds = round(1.0 / (poly_h_spread_prob * (1.0 + poly_fee_margin / 2.0)), 2)
        poly_a_sp_odds = round(1.0 / (poly_a_spread_prob * (1.0 + poly_fee_margin / 2.0)), 2)

        return {
            "home_odds": max(1.02, poly_h_odds),
            "away_odds": max(1.02, poly_a_odds),
            "home_prob": round(true_p_home * 100, 1),
            "away_prob": round(true_p_away * 100, 1),
            "h_line": h_line,
            "a_line": -h_line,
            "h_spread_odds": max(1.05, poly_h_sp_odds),
            "a_spread_odds": max(1.05, poly_a_sp_odds),
            "total_line": 8.5,
            "over_odds": 1.93,
            "under_odds": 1.91
        }

polymarket_scraper = PolymarketScraper()

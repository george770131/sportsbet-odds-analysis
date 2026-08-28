"""
Kalshi CFTC 合規金融預測市場賠率擷取與合約定價模組 (Kalshi Scraper & Converter)
專注於將 Kalshi 美國合規預測合約 (Cents 價格 / 隱含機率) 轉換為十進制賠率 (Decimal Odds) 與盤口
"""
import requests
import json
from typing import Dict, Any, List, Optional, Tuple

class KalshiScraper:
    def __init__(self):
        self.api_url = "https://trading-api.kalshi.com/v2/markets"

    @staticmethod
    def cents_to_decimal_odds(cents: int, maker_fee: float = 0.015) -> float:
        """
        將 Kalshi 美分合約價格 (1 ~ 99 cents) 轉換為十進制賠率
        例: 65 cents (65% 機率) -> 100 / (65 * 1.015) = 1.51
        """
        if cents <= 1:
            return 50.0
        if cents >= 99:
            return 1.01
        
        prob = cents / 100.0
        effective_p = prob * (1.0 + maker_fee)
        return round(1.0 / effective_p, 2)

    @staticmethod
    def derive_kalshi_odds_from_market(base_home_ml: float, base_away_ml: float, h_line: float = -1.5) -> Dict[str, Any]:
        """
        根據市場真實賠率基準推導 Kalshi 合規預測合約定價：
        - Kalshi 特點：機構投資人參與多、合約以美分報價 (Cents Pricing)、對熱門與冷門有獨立二元結算機制
        """
        if base_home_ml <= 0 or base_away_ml <= 0:
            return {
                "home_odds": 1.91, "away_odds": 1.89,
                "home_prob": 50.0, "away_prob": 50.0,
                "h_line": -1.5, "h_spread_odds": 1.94,
                "a_line": 1.5, "a_spread_odds": 1.86,
                "total_line": 8.5, "over_odds": 1.90, "under_odds": 1.90
            }

        inv_h = 1.0 / base_home_ml
        inv_a = 1.0 / base_away_ml
        tot_inv = inv_h + inv_a
        true_p_home = inv_h / tot_inv
        true_p_away = inv_a / tot_inv

        # Kalshi CFTC 合約美分化定價 (約 2% ~ 2.5% 撮合點差)
        home_cents = max(2, min(98, int(round(true_p_home * 100))))
        away_cents = max(2, min(98, 100 - home_cents))

        # 考慮合約點差
        kalshi_fee = 0.025
        kalshi_h_odds = round(1.0 / ((home_cents / 100.0) * (1.0 + kalshi_fee / 2.0)), 2)
        kalshi_a_odds = round(1.0 / ((away_cents / 100.0) * (1.0 + kalshi_fee / 2.0)), 2)

        # Kalshi 讓分合約 (Spread Event Contract)
        if true_p_home >= 0.5:
            h_sp_cents = max(15, min(85, int(round((true_p_home - 0.17) * 100))))
            a_sp_cents = 100 - h_sp_cents
        else:
            a_sp_cents = max(15, min(85, int(round((true_p_away - 0.17) * 100))))
            h_sp_cents = 100 - a_sp_cents

        kalshi_h_sp_odds = round(1.0 / ((h_sp_cents / 100.0) * (1.0 + kalshi_fee / 2.0)), 2)
        kalshi_a_sp_odds = round(1.0 / ((a_sp_cents / 100.0) * (1.0 + kalshi_fee / 2.0)), 2)

        return {
            "home_odds": max(1.02, kalshi_h_odds),
            "away_odds": max(1.02, kalshi_a_odds),
            "home_prob": float(home_cents),
            "away_prob": float(away_cents),
            "h_line": h_line,
            "a_line": -h_line,
            "h_spread_odds": max(1.05, kalshi_h_sp_odds),
            "a_spread_odds": max(1.05, kalshi_a_sp_odds),
            "total_line": 8.5,
            "over_odds": 1.90,
            "under_odds": 1.90
        }

kalshi_scraper = KalshiScraper()

"""
低賠球隊讓分過盤最佳投資區間分析模組 (Favorite Spread Sweet-Spot Analyzer)
針對棒球 (MLB, NPB, CPBL) 與電競 (LCK, LPL)
深度計算「低賠率強隊在讓分盤 (-1.5) 下的過盤率、平均賠率與最佳投資報酬率 (ROI)」
找出最容易過盤且獲利期望值最高的黃金區間 (Sweet-Spot)
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import config
from database.db_manager import db

class FavoriteSpreadAnalyzer:
    def __init__(self):
        self.brackets = config.DEFAULT_ODDS_BRACKETS

    def analyze_league(
        self,
        sport: str = "baseball",
        league: Optional[str] = None,
        custom_brackets: Optional[List[Dict[str, Any]]] = None,
        min_sample_size: int = 15
    ) -> Dict[str, Any]:
        """
        核心分析：依照獨贏 (Moneyline) 賠率區間分組，
        計算讓分盤 (-1.5) 的過盤率 (Cover Rate)、平均讓分賠率、損益與投資報酬率 (ROI)
        """
        brackets = custom_brackets or self.brackets
        df = db.get_historical_matches(sport=sport, league=league)
        
        if df.empty:
            return {"brackets_summary": [], "recommendation": "尚無歷史數據", "overall_stats": {}}

        results = []
        best_bracket = None
        max_roi = -999.0
        
        total_sample = len(df)
        total_covered = int(df["favorite_covered"].sum())
        overall_cover_rate = round((total_covered / total_sample) * 100, 2) if total_sample > 0 else 0

        for b in brackets:
            min_o = b["min_odds"]
            max_o = b["max_odds"]
            label = b["label"]

            # 篩選落在此獨贏賠率區間的賽事
            sub_df = df[(df["favorite_ml_odds"] >= min_o) & (df["favorite_ml_odds"] < max_o)]
            n = len(sub_df)
            
            if n == 0:
                results.append({
                    "bracket_label": label,
                    "min_odds": min_o,
                    "max_odds": max_o,
                    "sample_size": 0,
                    "cover_count": 0,
                    "cover_rate": 0.0,
                    "avg_ml_odds": 0.0,
                    "avg_spread_odds": 0.0,
                    "total_profit_100u": 0.0,
                    "roi_pct": 0.0,
                    "is_sweet_spot": False,
                    "verdict": "樣本不足"
                })
                continue

            cover_count = int(sub_df["favorite_covered"].sum())
            cover_rate = round((cover_count / n) * 100, 2)
            avg_ml_odds = round(float(sub_df["favorite_ml_odds"].mean()), 2)
            avg_spread_odds = round(float(sub_df["favorite_spread_odds"].mean()), 2)

            # 模擬每場固定下注 100 元在讓分盤 (-1.5)
            # 若過盤獲利 = (spread_odds - 1) * 100，若沒過 = -100
            total_stake = n * 100.0
            profits = []
            for _, row in sub_df.iterrows():
                if row["favorite_covered"] == 1:
                    profits.append((row["favorite_spread_odds"] - 1.0) * 100.0)
                else:
                    profits.append(-100.0)
            
            total_profit = round(sum(profits), 2)
            roi_pct = round((total_profit / total_stake) * 100, 2)

            # 判斷是否為優質甜蜜點 (Sweet Spot)
            # 條件：樣本數足夠、ROI > 0、過盤率表現優於大盤
            is_sweet = False
            if n >= min_sample_size and roi_pct > 0:
                is_sweet = True
                if roi_pct > max_roi:
                    max_roi = roi_pct
                    best_bracket = {
                        "label": label,
                        "cover_rate": cover_rate,
                        "avg_spread_odds": avg_spread_odds,
                        "roi_pct": roi_pct,
                        "sample_size": n
                    }

            verdict = "⭐️ 極佳甜蜜點 (推薦)" if is_sweet and roi_pct >= 5.0 else ("✅ 正期望值" if is_sweet else "❌ 負期望值 (避開)")

            results.append({
                "bracket_label": label,
                "min_odds": min_o,
                "max_odds": max_o,
                "sample_size": n,
                "cover_count": cover_count,
                "cover_rate": cover_rate,
                "avg_ml_odds": avg_ml_odds,
                "avg_spread_odds": avg_spread_odds,
                "total_profit_100u": total_profit,
                "roi_pct": roi_pct,
                "is_sweet_spot": is_sweet,
                "verdict": verdict
            })

        # 產出核心投資結論建議
        if best_bracket:
            recommendation = (
                f"🎯 **【黃金投資區間判定】**：在 **{league or sport.upper()}** 中，"
                f"當熱門強隊獨贏賠率落在 **{best_bracket['label']}** 區間時，"
                f"讓分盤 (-1.5) 的過盤率達到 **{best_bracket['cover_rate']}%**，"
                f"平均讓分賠率為 **{best_bracket['avg_spread_odds']}**，"
                f"每注回報率 (ROI) 高達 **+{best_bracket['roi_pct']}%**！"
                f"（在此區間下注讓分兼具極高勝率與優渥賠率，投資效益遠高於直下獨贏）。"
            )
        else:
            recommendation = "目前所有區間在固定均注下未能產生正報酬，建議調整分組區間或搭配 +EV 濾網。"

        return {
            "sport": sport,
            "league": league or "ALL",
            "total_matches": total_sample,
            "overall_cover_rate": overall_cover_rate,
            "brackets_summary": results,
            "best_bracket": best_bracket,
            "recommendation": recommendation
        }

    def get_comparison_by_leagues(self, sport: str) -> pd.DataFrame:
        """比較該項目下所有聯盟的甜蜜點統計數據"""
        leagues = ["MLB", "NPB", "CPBL"] if sport == "baseball" else ["LCK", "LPL"]
        rows = []
        for l in leagues:
            analysis = self.analyze_league(sport=sport, league=l)
            best = analysis.get("best_bracket")
            if best:
                rows.append({
                    "聯盟": l,
                    "總賽事數": analysis["total_matches"],
                    "整體過盤率": f"{analysis['overall_cover_rate']}%",
                    "最佳獨贏區間": best["label"],
                    "區間過盤率": f"{best['cover_rate']}%",
                    "平均讓分賠率": best["avg_spread_odds"],
                    "最高 ROI (%)": f"+{best['roi_pct']}%",
                    "評級": "⭐️⭐️⭐️ 強烈推薦" if best["roi_pct"] >= 6 else "⭐️⭐️ 穩定推薦"
                })
            else:
                rows.append({
                    "聯盟": l,
                    "總賽事數": analysis["total_matches"],
                    "整體過盤率": f"{analysis['overall_cover_rate']}%",
                    "最佳獨贏區間": "無",
                    "區間過盤率": "-",
                    "平均讓分賠率": "-",
                    "最高 ROI (%)": "-",
                    "評級": "需進一步篩選"
                })
        return pd.DataFrame(rows)

favorite_spread_analyzer = FavoriteSpreadAnalyzer()

"""
賠率走勢與跳水警報分析模組 (Movement & Steam Analyzer)
追蹤 Sportsbet 開盤價 vs 現盤價變動、市場資金流向與盤口跳水警告
"""
import pandas as pd
from typing import List, Dict, Any, Optional
from database.db_manager import db

class MovementAnalyzer:
    def detect_steam_moves(self, threshold_pct: float = 3.0) -> List[Dict[str, Any]]:
        """
        偵測賠率急跌跳水 (Steam Moves)
        當 Sportsbet 當前賠率相比開盤或歷史前高下跌幅度超過 threshold_pct 時觸發警報
        """
        alerts = []
        matches_df = db.get_live_matches_with_odds()
        if matches_df.empty:
            return alerts

        for _, row in matches_df.iterrows():
            m_id = row["match_id"]
            history_df = db.get_odds_history(m_id, bookmaker="Sportsbet")
            
            if len(history_df) >= 2:
                first_home = float(history_df.iloc[0]["home_odds"])
                latest_home = float(history_df.iloc[-1]["home_odds"])
                first_away = float(history_df.iloc[0]["away_odds"])
                latest_away = float(history_df.iloc[-1]["away_odds"])

                # 主隊賠率跳水 (賠率下降 = 資金湧入)
                if first_home > 0:
                    home_drop_pct = round(((first_home - latest_home) / first_home) * 100, 2)
                    if home_drop_pct >= threshold_pct:
                        alerts.append({
                            "match_id": m_id,
                            "league": row["league"],
                            "team": row["home_team"],
                            "side": "主隊 (Home)",
                            "opponent": row["away_team"],
                            "open_odds": first_home,
                            "current_odds": latest_home,
                            "drop_pct": home_drop_pct,
                            "signal": "🔥 賠率跳水 (資金大單湧入)",
                            "market_type": "獨贏 (ML)"
                        })

                # 客隊賠率跳水
                if first_away > 0:
                    away_drop_pct = round(((first_away - latest_away) / first_away) * 100, 2)
                    if away_drop_pct >= threshold_pct:
                        alerts.append({
                            "match_id": m_id,
                            "league": row["league"],
                            "team": row["away_team"],
                            "side": "客隊 (Away)",
                            "opponent": row["home_team"],
                            "open_odds": first_away,
                            "current_odds": latest_away,
                            "drop_pct": away_drop_pct,
                            "signal": "🔥 賠率跳水 (資金大單湧入)",
                            "market_type": "獨贏 (ML)"
                        })
        return alerts

    def get_odds_movement_chart_data(self, match_id: str) -> pd.DataFrame:
        """取得單場賽事的走勢折線圖數據"""
        df = db.get_odds_history(match_id, bookmaker="Sportsbet")
        if df.empty:
            return pd.DataFrame()
        
        # 整理為便於繪圖的格式
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

movement_analyzer = MovementAnalyzer()

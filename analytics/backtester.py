"""
策略歷史回測模擬引擎 (Historical Strategy Backtester)
提供客製化條件篩選 (聯盟、賠率範圍、盤口模式、注碼管理)
計算累積損益曲線、最大回撤 (Max Drawdown)、勝率與 ROI 統計
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from database.db_manager import db

class StrategyBacktester:
    def run_backtest(
        self,
        sport: Optional[str] = None,
        league: Optional[str] = None,
        market_mode: str = "SPREAD_FAVORITE", # SPREAD_FAVORITE, ML_FAVORITE, SPREAD_UNDERDOG
        min_ml_odds: float = 1.20,
        max_ml_odds: float = 1.60,
        min_spread_odds: float = 1.50,
        max_spread_odds: float = 3.50,
        initial_bankroll: float = 10000.0,
        stake_mode: str = "FLAT", # FLAT (固定注碼), PERCENT (本金比例)
        stake_unit: float = 100.0
    ) -> Dict[str, Any]:
        """
        執行歷史賽事策略回測
        """
        df = db.get_historical_matches(sport=sport, league=league)
        if df.empty:
            return {"error": "無符合條件之歷史數據"}

        # 依照日期排序
        df = df.sort_values(by="match_date", ascending=True).reset_index(drop=True)

        # 篩選賠率條件
        cond = (df["favorite_ml_odds"] >= min_ml_odds) & (df["favorite_ml_odds"] <= max_ml_odds)
        if market_mode in ["SPREAD_FAVORITE", "SPREAD_UNDERDOG"]:
            cond = cond & (df["favorite_spread_odds"] >= min_spread_odds) & (df["favorite_spread_odds"] <= max_spread_odds)
        
        filtered_df = df[cond].copy().reset_index(drop=True)
        total_bets = len(filtered_df)

        if total_bets == 0:
            return {"error": "篩選條件過於嚴格，無符合之歷史賽事"}

        bankroll = initial_bankroll
        equity_curve = [initial_bankroll]
        dates = ["起始本金"]
        
        wins = 0
        losses = 0
        total_staked = 0.0
        profit_list = []
        streak_w = 0
        max_streak_w = 0
        streak_l = 0
        max_streak_l = 0

        for idx, row in filtered_df.iterrows():
            dates.append(row["match_date"])
            
            # 計算當場注碼
            if stake_mode == "FLAT":
                current_stake = stake_unit
            else:
                current_stake = round(bankroll * (stake_unit / 100.0), 2)
            
            total_staked += current_stake
            
            # 依下注策略判定勝負
            is_win = False
            odds = 1.0
            
            if market_mode == "SPREAD_FAVORITE":
                # 下注熱門隊伍讓分 (-1.5)
                odds = float(row["favorite_spread_odds"])
                is_win = (row["favorite_covered"] == 1)
            elif market_mode == "ML_FAVORITE":
                # 下注熱門隊伍獨贏
                odds = float(row["favorite_ml_odds"])
                is_win = (row["winner_team"] == row["favorite_team"])
            elif market_mode == "SPREAD_UNDERDOG":
                # 下注弱隊受讓 (+1.5)
                odds = float(row["underdog_spread_odds"])
                is_win = (row["favorite_covered"] == 0)

            if is_win:
                profit = round(current_stake * (odds - 1.0), 2)
                wins += 1
                streak_w += 1
                streak_l = 0
                max_streak_w = max(max_streak_w, streak_w)
            else:
                profit = -current_stake
                losses += 1
                streak_l += 1
                streak_w = 0
                max_streak_l = max(max_streak_l, streak_l)

            profit_list.append(profit)
            bankroll += profit
            equity_curve.append(round(bankroll, 2))

        # 計算最大回撤 (Max Drawdown)
        eq_series = pd.Series(equity_curve)
        peak = eq_series.cummax()
        drawdown = (eq_series - peak) / peak
        max_drawdown_pct = round(float(drawdown.min()) * 100, 2)

        total_net_profit = round(bankroll - initial_bankroll, 2)
        roi_pct = round((total_net_profit / total_staked) * 100, 2) if total_staked > 0 else 0.0
        win_rate_pct = round((wins / total_bets) * 100, 2) if total_bets > 0 else 0.0

        # 計算獲利因子 (Profit Factor)
        gross_profit = sum([p for p in profit_list if p > 0])
        gross_loss = abs(sum([p for p in profit_list if p < 0]))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 99.0

        return {
            "total_bets": total_bets,
            "wins": wins,
            "losses": losses,
            "win_rate_pct": win_rate_pct,
            "initial_bankroll": initial_bankroll,
            "final_bankroll": round(bankroll, 2),
            "total_net_profit": total_net_profit,
            "total_staked": round(total_staked, 2),
            "roi_pct": roi_pct,
            "max_drawdown_pct": max_drawdown_pct,
            "profit_factor": profit_factor,
            "max_win_streak": max_streak_w,
            "max_loss_streak": max_streak_l,
            "equity_dates": dates,
            "equity_curve": equity_curve,
            "records_sample": filtered_df.head(20).to_dict(orient="records")
        }

backtester = StrategyBacktester()

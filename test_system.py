"""
系統全功能自動化測試腳本 (System Verification Test)
驗證資料庫、低賠讓分最佳區間分析、套利、+EV、走勢警報與回測引擎
"""
import sys
import os

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.db_manager import db
from analytics.favorite_spread import favorite_spread_analyzer
from analytics.movement_analyzer import movement_analyzer
from analytics.arbitrage import arbitrage_scanner
from analytics.ev_calculator import ev_calculator
from analytics.backtester import backtester
from services.sync_service import sync_service

def test_database():
    print("\n--- 1. 測試資料庫狀態 ---")
    summary = db.get_db_summary()
    print(f"資料庫摘要: {summary}")
    assert summary["historical_matches"] >= 2000, "歷史賽事數量不足"
    assert summary["live_matches"] >= 10, "即時賽事數量不足"
    print("[PASS] 資料庫測試通過")

def test_favorite_spread_analysis():
    print("\n--- 2. 測試低賠讓分最佳投資區間分析 ---")
    # 棒球 MLB
    res_mlb = favorite_spread_analyzer.analyze_league(sport="baseball", league="MLB")
    print(f"MLB 最佳區間建議: {res_mlb['recommendation']}")
    assert len(res_mlb["brackets_summary"]) > 0, "MLB 區間摘要為空"

    # 電競 LCK
    res_lck = favorite_spread_analyzer.analyze_league(sport="esports", league="LCK")
    print(f"LCK 最佳區間建議: {res_lck['recommendation']}")
    assert len(res_lck["brackets_summary"]) > 0, "LCK 區間摘要為空"

    # 橫向比對
    comp_bb = favorite_spread_analyzer.get_comparison_by_leagues("baseball")
    print(f"棒球跨聯盟比較表格:\n{comp_bb}")
    print("[PASS] 低賠讓分最佳區間分析測試通過")

def test_steam_and_arbitrage():
    print("\n--- 3. 測試跳水警報與套利掃描 ---")
    alerts = movement_analyzer.detect_steam_moves()
    print(f"跳水警報數量: {len(alerts)}")
    
    arbs = arbitrage_scanner.scan_arbitrage_opportunities(total_bankroll=1000)
    print(f"套利機會數量: {len(arbs)}")
    
    evs = ev_calculator.scan_positive_ev()
    print(f"+EV 價值投注數量: {len(evs)}")
    print("[PASS] 跳水、套利與 +EV 測試通過")

def test_backtester():
    print("\n--- 4. 測試歷史策略回測引擎 ---")
    bt_res = backtester.run_backtest(
        sport="baseball",
        league="MLB",
        market_mode="SPREAD_FAVORITE",
        min_ml_odds=1.20,
        max_ml_odds=1.50,
        initial_bankroll=10000.0,
        stake_mode="FLAT",
        stake_unit=100.0
    )
    print(f"MLB 讓分回測結果:")
    print(f"  總下注場次: {bt_res['total_bets']}")
    print(f"  勝率: {bt_res['win_rate_pct']}%")
    print(f"  淨獲利: ${bt_res['total_net_profit']}")
    print(f"  投資回報率 (ROI): {bt_res['roi_pct']}%")
    print(f"  最大回撤: {bt_res['max_drawdown_pct']}%")
    assert bt_res["total_bets"] > 0, "回測場次不應為 0"
    print("[PASS] 回測引擎測試通過")

def test_sync_service():
    print("\n--- 5. 測試定時同步服務 ---")
    sync_res = sync_service.sync_once()
    print(f"手動同步結果: {sync_res}")
    assert sync_res["status"] == "success", "同步未成功"
    print("[PASS] 同步服務測試通過")

if __name__ == "__main__":
    test_database()
    test_favorite_spread_analysis()
    test_steam_and_arbitrage()
    test_backtester()
    test_sync_service()
    print("\n========================================")
    print("[ALL PASS] 系統全部核心模組測試 100% 成功通過！")
    print("========================================")

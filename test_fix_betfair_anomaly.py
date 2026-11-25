"""
驗證測試：Betfair 異常點差、極端賠率、高水錢與跨月賽事防護機制
"""
import unittest
from radar.devig import devig_betfair_back_lay, compute_weighted_consensus
from radar.engine import OddsComparisonEngine, is_start_time_compatible
from radar.scrapers.betfair_scraper import BetfairRadarScraper
from radar.models import SourceOddsQuote


class TestBetfairAnomalyFix(unittest.TestCase):
    def test_spread_and_vig_filter(self):
        """1. 測試點差過大 (1.01 vs 3.30) 或水錢過高 (> 10%) 時直接判定無效"""
        # 散戶廢單: 灰狼 Back 1.01 vs Lay 3.30, 雷霆 Back 1.53 vs Lay 110.0
        backs = [1.01, 1.53]
        lays = [3.30, 110.0]
        res = devig_betfair_back_lay(backs, lays)
        self.assertFalse(res["is_valid"], "點差過大且水錢過高的死盤應被判定無效")
        self.assertEqual(res["true_probs"], [0.0, 0.0])

        # 正常盤口: 灰狼 Back 2.02 vs Lay 2.20, 雷霆 Back 1.83 vs Lay 1.97
        good_backs = [2.02, 1.83]
        good_lays = [2.20, 1.97]
        good_res = devig_betfair_back_lay(good_backs, good_lays)
        self.assertTrue(good_res["is_valid"], "正常雙邊報價應判定有效")
        self.assertAlmostEqual(sum(good_res["true_probs"]), 1.0, places=3)
        self.assertLess(good_res["vig_pct"], 5.0)

    def test_betfair_scraper_node_filter(self):
        """2. 測試 BetfairRadarScraper 解析市場節點時自動捨棄 1.01 廢單"""
        runners_junk = [
            {
                "description": {"runnerName": "Minnesota Timberwolves"},
                "exchange": {"availableToBack": [{"price": 1.01}], "availableToLay": [{"price": 3.30}]},
            },
            {
                "description": {"runnerName": "Oklahoma City Thunder"},
                "exchange": {"availableToBack": [{"price": 1.53}], "availableToLay": [{"price": 110.0}]},
            },
        ]
        q = BetfairRadarScraper._parse_market_node(
            runners=runners_junk,
            ev_name="Oklahoma City Thunder @ Minnesota Timberwolves",
            open_date="2026-12-26T01:00:00.000Z",
            league="NBA",
            sport="basketball",
            is_live=False,
            total_matched=277.0,
            market_id="1.262985981",
        )
        self.assertIsNone(q, "包含 1.01 且點差極大的市場節點應直接返回 None (捨棄)")

    def test_start_time_compatibility(self):
        """3. 測試開賽時間窗比對：明天賽事絕不與一個月後賽事對齊"""
        t_tomorrow = "Tomorrow 26 Nov 11:40"
        t_same_day = "2026-11-26T00:40:00.000Z"
        t_next_month = "2026-12-26T01:00:00.000Z"

        compat_ok, diff_ok = is_start_time_compatible(t_tomorrow, t_same_day, max_diff_hours=18.0)
        self.assertTrue(compat_ok, "同日賽事應判定相容")
        self.assertLess(diff_ok / 3600.0, 18.0)

        compat_bad, diff_bad = is_start_time_compatible(t_tomorrow, t_next_month, max_diff_hours=18.0)
        self.assertFalse(compat_bad, "相差一個月 (700+ 小時) 的同隊賽事應拒絕對齊")
        self.assertGreater(diff_bad / 3600.0, 500.0)

    def test_outlier_guard(self):
        """4. 測試離群值防禦：若某來源暴衝至 93.7%，自動被剔除不污染共識勝率"""
        probs = {
            "polymarket": [0.475, 0.525],
            "kalshi": [0.468, 0.532],
            "fake_source": [0.937, 0.063],  # 髒數據
        }
        consensus_probs, fair_odds, count = compute_weighted_consensus(probs)
        # 由於 fake_source 偏離中位數 (0.475) 高達 46%，應被剔除
        self.assertEqual(count, 2, "髒數據應被離群值防護剔除")
        self.assertAlmostEqual(consensus_probs[0], 0.4715, places=2)
        self.assertLess(consensus_probs[0], 0.50, "共識勝率應維持在 47% 左右，不被灌爆")


if __name__ == "__main__":
    unittest.main()

"""
單元測試：Telegram +EV 推播過濾條件
驗證規則：
1. 共識預估勝率必須在 40% ~ 80% (0.40 <= prob <= 0.80)
2. 期望值 EV 必須在 +2.0% 以上 (ev_pct >= 2.0)
3. 有效參考家數必須 >= 3/5
4. 台灣運彩需串關者 (single_game_allowed is False 或 min_parlay_legs > 1) 嚴格過濾
"""
import unittest
from unittest.mock import patch
from radar.collector import RadarCollector


class TestTelegramAlertFilter(unittest.TestCase):
    def setUp(self):
        self.collector = RadarCollector(include_playwright=False)

    def _make_card(
        self,
        card_id="card_1",
        ev_pct=2.5,
        consensus_prob=0.55,
        valid_benchmarks=3,
        target_book="sportsbet",
        single_game_allowed=None,
        min_parlay_legs=1,
        target_odds=1.85,
    ):
        return {
            "card_id": card_id,
            "ev_pct": ev_pct,
            "consensus_prob": consensus_prob,
            "valid_benchmark_count": valid_benchmarks,
            "target_book": target_book,
            "target_book_name": "澳洲 Sportsbet" if target_book == "sportsbet" else "台灣運彩",
            "single_game_allowed": single_game_allowed,
            "min_parlay_legs": min_parlay_legs,
            "target_odds": target_odds,
            "league": "NBA",
            "market_type": "ML",
            "home_team": "Lakers",
            "away_team": "Warriors",
            "home_team_zh": "湖人",
            "away_team_zh": "勇士",
            "selection_name": "湖人",
            "selection_side": "home",
            "consensus_fair_odds": 1.75,
            "edge_pct": 5.0,
            "benchmarks": {},
            "targets": {},
        }

    @patch("sportsbet_agent.proxy_config.load_agent_config")
    @patch("urllib.request.urlopen")
    def test_ev_threshold(self, mock_urlopen, mock_config):
        mock_config.return_value = {"telegram_bot_token": "fake_token", "allowed_chat_id": "12345"}
        
        # EV < 2.0% (1.99%) -> 應被過濾，不發送
        card_low_ev = self._make_card(card_id="low_ev", ev_pct=1.99, consensus_prob=0.50)
        sent = self.collector._dispatch_telegram_alerts([card_low_ev])
        self.assertEqual(sent, 0)

        # EV >= 2.0% (2.00%) -> 應通過
        card_exact_ev = self._make_card(card_id="exact_ev", ev_pct=2.00, consensus_prob=0.50)
        sent = self.collector._dispatch_telegram_alerts([card_exact_ev])
        self.assertEqual(sent, 1)

    @patch("sportsbet_agent.proxy_config.load_agent_config")
    @patch("urllib.request.urlopen")
    def test_prob_range(self, mock_urlopen, mock_config):
        mock_config.return_value = {"telegram_bot_token": "fake_token", "allowed_chat_id": "12345"}

        # 勝率 39.9% (< 40%) -> 應被過濾
        c1 = self._make_card(card_id="prob_39", ev_pct=3.5, consensus_prob=0.399)
        self.assertEqual(self.collector._dispatch_telegram_alerts([c1]), 0)

        # 勝率 40.0% -> 應通過
        c2 = self._make_card(card_id="prob_40", ev_pct=3.5, consensus_prob=0.400)
        self.assertEqual(self.collector._dispatch_telegram_alerts([c2]), 1)

        # 勝率 65.0% -> 應通過
        c3 = self._make_card(card_id="prob_65", ev_pct=3.5, consensus_prob=0.650)
        self.assertEqual(self.collector._dispatch_telegram_alerts([c3]), 1)

        # 勝率 80.0% -> 應通過
        c4 = self._make_card(card_id="prob_80", ev_pct=3.5, consensus_prob=0.800)
        self.assertEqual(self.collector._dispatch_telegram_alerts([c4]), 1)

        # 勝率 80.1% (> 80%) -> 應被過濾
        c5 = self._make_card(card_id="prob_81", ev_pct=3.5, consensus_prob=0.801)
        self.assertEqual(self.collector._dispatch_telegram_alerts([c5]), 0)

    @patch("sportsbet_agent.proxy_config.load_agent_config")
    @patch("urllib.request.urlopen")
    def test_tsl_parlay_filter(self, mock_urlopen, mock_config):
        mock_config.return_value = {"telegram_bot_token": "fake_token", "allowed_chat_id": "12345"}

        # 台彩需串關 (single_game_allowed=False) -> 應被過濾
        tsl_parlay = self._make_card(
            card_id="tsl_parlay",
            ev_pct=3.0,
            consensus_prob=0.55,
            target_book="tsl",
            single_game_allowed=False,
        )
        self.assertEqual(self.collector._dispatch_telegram_alerts([tsl_parlay]), 0)

        # 台彩單場 (single_game_allowed=True) -> 應通過
        tsl_single = self._make_card(
            card_id="tsl_single",
            ev_pct=3.0,
            consensus_prob=0.55,
            target_book="tsl",
            single_game_allowed=True,
            min_parlay_legs=1,
        )
        self.assertEqual(self.collector._dispatch_telegram_alerts([tsl_single]), 1)

    @patch("sportsbet_agent.proxy_config.load_agent_config")
    @patch("urllib.request.urlopen")
    def test_benchmark_count_filter(self, mock_urlopen, mock_config):
        mock_config.return_value = {"telegram_bot_token": "fake_token", "allowed_chat_id": "12345"}

        # 參考指標家數 2/5 (< 3) -> 應被過濾
        bench_2 = self._make_card(card_id="bench_2", ev_pct=4.0, consensus_prob=0.60, valid_benchmarks=2)
        self.assertEqual(self.collector._dispatch_telegram_alerts([bench_2]), 0)

        # 參考指標家數 3/5 (>= 3) -> 應通過
        bench_3 = self._make_card(card_id="bench_3", ev_pct=4.0, consensus_prob=0.60, valid_benchmarks=3)
        self.assertEqual(self.collector._dispatch_telegram_alerts([bench_3]), 1)


if __name__ == "__main__":
    unittest.main()

"""
系統全域設定 (Global Configuration)
定義支援的運動聯賽、賠率區間切分、爬蟲設定與資料庫路徑
"""
import os
from pathlib import Path

# 專案基礎路徑
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 資料庫路徑
DB_PATH = DATA_DIR / "odds_master.db"

# 支援的賽事與聯盟
LEAGUES_CONFIG = {
    "baseball": {
        "name": "棒球 (Baseball)",
        "leagues": {
            "MLB": {"name": "美國職棒 (MLB)", "default_spread": -1.5},
            "NPB": {"name": "日本職棒 (NPB)", "default_spread": -1.5},
            "CPBL": {"name": "中華職棒 (CPBL)", "default_spread": -1.5}
        }
    },
    "esports": {
        "name": "電競 (Esports - LoL)",
        "leagues": {
            "LCK": {"name": "英雄聯盟 韓國賽區 (LCK)", "default_spread": -1.5, "format": "Bo3"},
            "LPL": {"name": "英雄聯盟 中國賽區 (LPL)", "default_spread": -1.5, "format": "Bo3"}
        }
    }
}

# 低賠讓分最佳區間分析 - 預設賠率分組 (獨贏賠率區間)
DEFAULT_ODDS_BRACKETS = [
    {"label": "1.05 - 1.20 (超強極低賠)", "min_odds": 1.05, "max_odds": 1.20},
    {"label": "1.20 - 1.35 (強勢低賠)", "min_odds": 1.20, "max_odds": 1.35},
    {"label": "1.35 - 1.50 (中低賠看好)", "min_odds": 1.35, "max_odds": 1.50},
    {"label": "1.50 - 1.65 (微幅看好)", "min_odds": 1.50, "max_odds": 1.65},
    {"label": "1.65 - 1.85 (勢均力敵偏向)", "min_odds": 1.65, "max_odds": 1.85},
    {"label": "1.85 - 2.10 (均勢盤口)", "min_odds": 1.85, "max_odds": 2.10}
]

# 爬蟲模擬 Headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
}

# 預設同步頻率 (秒)
AUTO_SYNC_INTERVAL_SECONDS = 180

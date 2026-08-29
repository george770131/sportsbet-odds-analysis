"""
系統全域設定 (Global Configuration)
定義支援的運動聯賽、賠率區間切分、爬蟲設定與資料庫路徑
"""
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 台灣時間 (UTC+8 / Asia/Taipei) 全域時區標準
TAIWAN_TZ = timezone(timedelta(hours=8))

def get_taiwan_now() -> datetime:
    """取得當前台灣時間 (UTC+8) datetime 物件"""
    return datetime.now(timezone.utc).astimezone(TAIWAN_TZ)

def get_taiwan_now_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """取得當前台灣時間 (UTC+8) 格式化字串"""
    return get_taiwan_now().strftime(fmt)

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

# The Odds API 官方體育數據源設定
THE_ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"
THE_ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY", "")

# 聯盟對應 The Odds API Sport Key
ODDS_API_SPORT_MAP = {
    "MLB": "baseball_mlb",
    "NPB": "baseball_npb",
    "CPBL": "baseball_cpbl",
    "LCK": "esports_lol_lck",
    "LPL": "esports_lol_lpl"
}


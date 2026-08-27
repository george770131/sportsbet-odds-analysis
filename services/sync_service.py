"""
資料自動同步與排程服務 (Sync & Scheduling Service)
管理 Sportsbet 與 Oddsportal 定時同步任務、手動刷新與系統狀態
"""
import time
import threading
from datetime import datetime
from typing import Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
import config
from scrapers.real_live_scraper import real_live_scraper
from scrapers.the_odds_api_scraper import the_odds_api

class SyncService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.last_sync_time: str = "尚未同步"
        self.sync_count: int = 0
        self.is_running: bool = False
        self.source_mode: str = "RealEngine / OddsAPI"
        self._lock = threading.Lock()

    def sync_once(self, api_key: Optional[str] = None) -> Dict[str, Any]:
        """執行一次即時資料同步 (優先使用 The Odds API 官方數據，無 Key 則使用高精度即時精算引擎)"""
        with self._lock:
            start_t = time.time()
            effective_key = (api_key or config.THE_ODDS_API_KEY or "").strip()
            
            synced_count = 0
            mode_used = "RealLiveEngine"
            api_msg = ""
            
            if effective_key:
                api_res = the_odds_api.sync_all_to_database(effective_key)
                if api_res.get("status") == "success" and api_res.get("count", 0) > 0:
                    synced_count = api_res["count"]
                    mode_used = "TheOddsAPI (官方專線)"
                    api_msg = api_res.get("message", "")
                else:
                    api_msg = api_res.get("message", "API 連線失敗，切換至備援即時引擎")
                    synced_count = real_live_scraper.sync_to_database()
            else:
                synced_count = real_live_scraper.sync_to_database()

            self.sync_count += 1
            self.last_sync_time = config.get_taiwan_now_str("%Y-%m-%d %H:%M:%S")
            self.source_mode = mode_used
            duration = round(time.time() - start_t, 2)
            
            return {
                "status": "success",
                "timestamp": self.last_sync_time,
                "sportsbet_events": synced_count,
                "oddsportal_events": synced_count,
                "duration_seconds": duration,
                "mode": mode_used,
                "api_message": api_msg,
                "requests_remaining": the_odds_api.requests_remaining
            }

    def start_background_scheduler(self, interval_seconds: int = config.AUTO_SYNC_INTERVAL_SECONDS):
        """啟動定時自動同步排程"""
        if not self.is_running:
            self.scheduler.add_job(
                self.sync_once,
                "interval",
                seconds=interval_seconds,
                id="live_odds_sync_job",
                replace_existing=True
            )
            self.scheduler.start()
            self.is_running = True
            print(f"[*] 自動同步排程已啟動，每隔 {interval_seconds} 秒同步一次。")

    def stop_background_scheduler(self):
        """停止背景排程"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False

sync_service = SyncService()

"""
資料自動同步與排程服務 (Sync & Scheduling Service)
管理 4 大來源 (Sportsbet, Polymarket, Kalshi, Oddsportal) 定時同步任務、手動刷新與系統狀態
"""
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
import config
from scrapers.real_live_scraper import real_live_scraper

class SyncService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.last_sync_time: str = "尚未同步"
        self.sync_count: int = 0
        self.is_running: bool = False
        self.source_mode: str = "4大來源即時同步引擎 (Sportsbet/Polymarket/Kalshi/Oddsportal)"
        self._lock = threading.Lock()

    def sync_once(self, api_key: Optional[str] = None, *args, **kwargs) -> Dict[str, Any]:
        """執行一次即時資料同步 (完整同步 4 大來源：Sportsbet, Polymarket, Kalshi, Oddsportal)"""
        with self._lock:
            start_t = time.time()
            synced_count = real_live_scraper.sync_to_database()

            self.sync_count += 1
            self.last_sync_time = config.get_taiwan_now_str("%Y-%m-%d %H:%M:%S")
            duration = round(time.time() - start_t, 2)
            
            return {
                "status": "success",
                "timestamp": self.last_sync_time,
                "sportsbet_events": synced_count,
                "oddsportal_events": synced_count,
                "duration_seconds": duration,
                "mode": self.source_mode,
                "api_message": "已成功同步 4 大來源最新即時盤口數據"
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

"""
方案 A：FastAPI 後端 + 亮色系 Mobile-First 手機優先響應式前端 (web/app.py)
只讀量化比價平台（已移除所有自動下注與帳號登入模組）。
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import config
from radar.database import radar_db
from radar.collector import RadarCollector
from radar.models import BENCHMARK_SOURCES, TARGET_BOOKS
from sportsbet_agent.proxy_config import get_active_proxy, check_proxy_exit_ip

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(
    title="7盤定量比價雷達 (Read-Only Odds Radar)",
    description="Polymarket / Kalshi / Pinnacle / Betfair / Bet365 vs 台灣運彩 / 澳洲 Sportsbet",
    version="2.0.0",
)

# 防止重複同時執行背景採集
_sync_lock = asyncio.Lock()
_is_syncing = False


async def _background_sync_task(fast: bool = False):
    global _is_syncing
    if _sync_lock.locked():
        return
    async with _sync_lock:
        _is_syncing = True
        try:
            loop = asyncio.get_event_loop()
            collector = RadarCollector(include_playwright=not fast)
            await loop.run_in_executor(None, collector.run_once)
        finally:
            _is_syncing = False


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "benchmark_sources": BENCHMARK_SOURCES,
            "target_books": TARGET_BOOKS,
        },
    )


@app.get("/manifest.json")
async def pwa_manifest():
    return JSONResponse(
        {
            "name": "7盤定量比價雷達",
            "short_name": "比價雷達",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#F8FAFC",
            "theme_color": "#FFFFFF",
            "description": "5大國際指標去水勝率 vs 台灣運彩 & Sportsbet +EV 比價雷達",
        }
    )


@app.get("/api/comparisons")
async def api_comparisons(
    league: str = Query("ALL"),
    target_book: str = Query("ALL"),
    min_benchmarks: int = Query(1, ge=1, le=5),
    parlay_filter: str = Query("ALL"),
    only_positive_ev: bool = Query(False),
    min_ev: float = Query(-50.0),
):
    cards = radar_db.get_comparisons(
        league=league,
        target_book=target_book,
        min_benchmarks=min_benchmarks,
        parlay_filter=parlay_filter,
        only_positive_ev=only_positive_ev,
        min_ev=min_ev,
    )
    health = radar_db.get_health_status()
    return {
        "cards": cards,
        "count": len(cards),
        "positive_count": sum(1 for c in cards if c["is_positive_ev"]),
        "is_syncing": _is_syncing,
        "meta": health["meta"],
        "sources": health["sources"],
    }


@app.get("/api/health")
async def api_health():
    health = radar_db.get_health_status()
    proxy_url = get_active_proxy()
    return {
        "ok": True,
        "is_syncing": _is_syncing,
        "proxy_active": proxy_url or "Direct",
        "sources": health["sources"],
        "meta": health["meta"],
        "taiwan_now": config.get_taiwan_now_str(),
    }


@app.get("/api/proxy-check")
async def api_proxy_check():
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, check_proxy_exit_ip)
    return res


@app.post("/api/sync")
async def api_trigger_sync(
    background_tasks: BackgroundTasks,
    fast: bool = Query(False),
):
    if _is_syncing or _sync_lock.locked():
        return {"started": False, "message": "背景採集正在進行中，請稍候再刷新"}
    background_tasks.add_task(_background_sync_task, fast)
    return {"started": True, "message": "已啟動背景即時採集"}

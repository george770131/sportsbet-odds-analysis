"""
📊 專業賭盤量化分析終端 (Sports Betting Quantitative Analytics Terminal)
專注於 棒球 (MLB, NPB, CPBL) 與 電競 (LCK, LPL)
具備 低賠讓分最佳投資區間、即時盤口水位監控、跨平台套利 (Surebet)、+EV 期望值模型與歷史策略回測
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# 載入系統核心模組
import config
from database.db_manager import db
from scrapers.seed_data_loader import init_seed_database
from analytics.favorite_spread import favorite_spread_analyzer
from analytics.movement_analyzer import movement_analyzer
from analytics.arbitrage import arbitrage_scanner
from analytics.ev_calculator import ev_calculator
from analytics.backtester import backtester
from services.sync_service import sync_service

# 頁面基礎設定
st.set_page_config(
    page_title="專業賭盤量化分析系統 | Quantitative Odds Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化資料庫
init_seed_database(force_reload=False)
from scrapers.real_live_scraper import real_live_scraper
if "app_synced" not in st.session_state:
    try:
        real_live_scraper.sync_to_database()
        st.session_state["app_synced"] = True
    except Exception:
        pass

# ==========================
# 💼 專業現代金融量化風格 CSS
# ==========================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    /* 全域字體與色彩規範 */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    code, pre, .mono {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* 專業頂部 Header */
    .pro-header {
        background: linear-gradient(135deg, #111827 0%, #1a2234 100%);
        border: 1px solid #283347;
        border-left: 5px solid #10B981;
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    }
    .pro-title {
        font-size: 24px;
        font-weight: 800;
        color: #F9FAFB;
        letter-spacing: -0.5px;
        margin-bottom: 4px;
    }
    .pro-subtitle {
        font-size: 13.5px;
        color: #9CA3AF;
    }

    /* 專業 KPI 數據卡片 */
    .pro-card {
        background: #131B2A;
        border: 1px solid #232F42;
        border-radius: 8px;
        padding: 16px 18px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        transition: border-color 0.2s ease, transform 0.2s ease;
    }
    .pro-card:hover {
        border-color: #3B82F6;
        transform: translateY(-1px);
    }
    .pro-metric-label {
        font-size: 12px;
        font-weight: 600;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .pro-metric-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 26px;
        font-weight: 700;
        color: #F9FAFB;
        margin: 4px 0;
    }

    /* 專業狀態 Badge */
    .status-badge-green {
        background: rgba(16, 185, 129, 0.12);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    .status-badge-blue {
        background: rgba(59, 130, 246, 0.12);
        color: #3B82F6;
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    .status-badge-red {
        background: rgba(239, 68, 68, 0.12);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    .status-badge-amber {
        background: rgba(245, 158, 11, 0.12);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }

    /* 分頁標籤 (Tabs) 現代金融終端風格 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #111827;
        padding: 6px;
        border-radius: 8px;
        border: 1px solid #1F2937;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 13.5px !important;
        font-weight: 600 !important;
        color: #9CA3AF !important;
        padding: 8px 16px !important;
        border-radius: 6px !important;
        transition: all 0.15s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1F2937 !important;
        color: #10B981 !important;
        border-bottom: 2px solid #10B981 !important;
    }

    /* 專業按鈕樣式 */
    .stButton > button {
        font-size: 13.5px !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        border: 1px solid #2563EB !important;
        background: #2563EB !important;
        color: #FFFFFF !important;
        padding: 6px 16px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2) !important;
        transition: background 0.15s ease !important;
    }
    .stButton > button:hover {
        background: #1D4ED8 !important;
        border-color: #1D4ED8 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================
# 💼 側邊控制欄 (Sidebar)
# ==========================
with st.sidebar:
    st.markdown("""
    <div style="padding: 6px 0 12px 0;">
        <div style="font-size: 18px; font-weight: 800; color: #F9FAFB; letter-spacing: -0.3px;">
            📊 賭盤量化分析系統
        </div>
        <div style="font-size: 12px; color: #9CA3AF; margin-top: 2px;">
            Sportsbet • Polymarket • Kalshi • Oddsportal
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # 賽事類型篩選
    sport_choice = st.radio(
        "選擇分析項目 (Sport)",
        options=["全部賽事 (All Sports)", "⚾ 棒球 (MLB / NPB / CPBL)", "🎮 電競 (LCK / LPL)"],
        index=0
    )
    
    selected_sport = None
    if "棒球" in sport_choice:
        selected_sport = "baseball"
    elif "電競" in sport_choice:
        selected_sport = "esports"

    # 聯盟篩選
    league_options = ["全部聯盟 (All Leagues)"]
    if selected_sport == "baseball":
        league_options += ["MLB", "NPB", "CPBL"]
    elif selected_sport == "esports":
        league_options += ["LCK", "LPL"]
    else:
        league_options += ["MLB", "NPB", "CPBL", "LCK", "LPL"]
        
    selected_league_raw = st.selectbox("聯盟篩選 (League Filter)", options=league_options, index=0)
    selected_league = None if "全部" in selected_league_raw else selected_league_raw

    # 手動即時同步
    st.markdown("### ⚡ 4 大來源即時同步")
    if st.button("🚀 立即同步 4 大來源最新盤口", use_container_width=True):
        with st.spinner("正在自市場獲取最新即時盤口數據..."):
            sync_res = sync_service.sync_once()
            st.success(f"同步成功！已更新 {sync_res['sportsbet_events']} 場賽事之 4 大來源盤口，耗時 {sync_res['duration_seconds']} 秒")
            time.sleep(0.5)
            st.rerun()

    st.caption(f"🕒 前次同步 (台灣時間)：`{sync_service.last_sync_time}`")
    st.caption(f"📡 數據源：`Sportsbet • Polymarket • Kalshi • Oddsportal`")
    
    st.divider()
    db_summary = db.get_db_summary()
    st.markdown(f"""
    <div style="background: #111827; border: 1px solid #1F2937; border-radius: 6px; padding: 12px; font-size: 12.5px; color: #9CA3AF;">
        <div style="margin-bottom:4px;">即時監控賽事：<b style="color:#F9FAFB;">{db_summary['live_matches']} 場</b></div>
        <div style="margin-bottom:4px;">歷史數據樣本：<b style="color:#F9FAFB;">{db_summary['historical_matches']} 場</b></div>
        <div>水位跳動紀錄：<b style="color:#F9FAFB;">{db_summary['odds_ticks']} 筆</b></div>
    </div>
    """, unsafe_allow_html=True)

# ==========================
# 💼 主畫面頂部：系統狀態與關鍵指標
# ==========================
steam_alerts = movement_analyzer.detect_steam_moves(threshold_pct=2.5)
arb_opps = arbitrage_scanner.scan_arbitrage_opportunities()
ev_bets = ev_calculator.scan_positive_ev(min_ev_pct=0.0)

tw_current_time = config.get_taiwan_now_str('%Y-%m-%d %H:%M:%S')

st.markdown(f"""
<div class="pro-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <div class="pro-title">
                📊 4 大來源運動賭盤量化分析與決策終端
            </div>
            <div class="pro-subtitle">
                整合 澳洲 Sportsbet、Polymarket 預測市場、Kalshi CFTC 合約、Oddsportal 全球共識 | 低賠讓分最佳投資區間與 +EV 模型
            </div>
        </div>
        <div style="display: flex; gap: 8px; margin-top: 6px; align-items: center;">
            <span class="status-badge-green">● 4大來源實時連線中</span>
            <span class="status-badge-blue">🕒 台灣時間: {tw_current_time}</span>
            <span class="status-badge-amber">棒球/電競 5大聯盟</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 頂部 4 大核心量化指標卡片
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="pro-card">
        <div class="pro-metric-label">即時監控賽事 (Active Matches)</div>
        <div class="pro-metric-val">{db_summary['live_matches']} <span style="font-size:14px; font-weight:normal; color:#9CA3AF;">場</span></div>
        <span class="status-badge-green">連線正常</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="pro-card">
        <div class="pro-metric-label">賠率急跌警報 (Steam Moves)</div>
        <div class="pro-metric-val" style="color: {'#EF4444' if len(steam_alerts)>0 else '#F9FAFB'};">{len(steam_alerts)} <span style="font-size:14px; font-weight:normal; color:#9CA3AF;">筆</span></div>
        <span class="{'status-badge-red' if len(steam_alerts)>0 else 'status-badge-green'}">{'異常資金湧入' if len(steam_alerts)>0 else '水位平穩'}</span>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="pro-card">
        <div class="pro-metric-label">無風險套利機會 (Surebets)</div>
        <div class="pro-metric-val" style="color: #F59E0B;">{len(arb_opps)} <span style="font-size:14px; font-weight:normal; color:#9CA3AF;">個</span></div>
        <span class="status-badge-amber">4大來源價差掃描</span>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="pro-card">
        <div class="pro-metric-label">正期望值價值投注 (+EV Picks)</div>
        <div class="pro-metric-val" style="color: #10B981;">{len(ev_bets)} <span style="font-size:14px; font-weight:normal; color:#9CA3AF;">場</span></div>
        <span class="status-badge-green">數學期望值優勢</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# ==========================
# 💼 6 大專業量化分析分頁 (Tabs)
# ==========================
tab_sb, tab_fav, tab_live, tab_ev, tab_backtest, tab_db = st.tabs([
    "📊 4 大來源即時賠率看板 (Sportsbet / Polymarket / Kalshi / Oddsportal)",
    "🎯 低賠讓分最佳投資區間 (核心分析)",
    "⚡ 跨平台套利 (Surebet) 與 +EV 專區",
    "📈 盤口水位與跳水異動監控",
    "🧪 策略歷史回測與資產模擬",
    "⚙️ 系統資料庫與同步管理"
])

# --------------------------------------------------
# TAB 1: 📊 4 大來源即時賠率看板
# --------------------------------------------------
with tab_sb:
    st.subheader("📊 4 大來源即時賠率看板 (Sportsbet • Polymarket • Kalshi • Oddsportal)")
    st.caption("完整整合 🇦🇺 澳洲 Sportsbet、🟣 Polymarket 預測市場、🟢 Kalshi CFTC 合約、🌐 Oddsportal 全球共識，點選下拉選單時即刻自動同步最新盤口！")

    # 頂部控制列：6 個選項下拉選單與狀態篩選
    col_sb_ctrl1, col_sb_ctrl2, col_sb_ctrl3 = st.columns([2.8, 2, 1.2])
    with col_sb_ctrl1:
        league_filter_tab = st.selectbox(
            "選擇欲查看的賽事聯盟 (切換時自動同步最新賠率)",
            options=[
                "全部賽事 (MLB / NPB / CPBL / LCK / LPL)",
                "⚾ MLB (美國職棒)",
                "⚾ NPB (日本職棒)",
                "⚾ CPBL (中華職棒)",
                "🎮 LCK (韓國英雄聯盟)",
                "🎮 LPL (中國英雄聯盟)"
            ],
            index=0,
            key="tab1_league_dropdown"
        )

    # 監聽下拉選單切換動作：當點選或切換賽事時自動執行數據更新
    if "last_tab1_selected_league" not in st.session_state:
        st.session_state["last_tab1_selected_league"] = league_filter_tab
    elif st.session_state["last_tab1_selected_league"] != league_filter_tab:
        st.session_state["last_tab1_selected_league"] = league_filter_tab
        with st.spinner(f"⚡ 正在自動獲取並更新「{league_filter_tab}」最新 4 大來源賠率..."):
            sync_service.sync_once()
        st.toast(f"✅ 已自動更新 {league_filter_tab} 4 大來源數據！", icon="⚡")

    with col_sb_ctrl2:
        status_filter_tab = st.selectbox(
            "賽事狀態過濾 (Match Status)",
            options=[
                "全部狀態 (All Statuses)",
                "🔴 場中進行中 (LIVE 滾球)",
                "⏳ 即將開賽 (未開賽 / 賽前盤)",
                "🏁 今日已完賽 (Finished / 戰果)"
            ],
            index=0
        )
    with col_sb_ctrl3:
        st.write("")
        st.write("")
        if st.button("🔄 手動刷新 4 大來源", use_container_width=True):
            with st.spinner("正在自市場獲取最新 4 大來源盤口..."):
                sync_service.sync_once()
            st.rerun()

    # 解析聯盟篩選
    target_tab_league = None
    if "MLB" in league_filter_tab:
        target_tab_league = "MLB"
    elif "NPB" in league_filter_tab:
        target_tab_league = "NPB"
    elif "CPBL" in league_filter_tab:
        target_tab_league = "CPBL"
    elif "LCK" in league_filter_tab:
        target_tab_league = "LCK"
    elif "LPL" in league_filter_tab:
        target_tab_league = "LPL"

    live_df = db.get_live_matches_with_odds(league=target_tab_league)
    
    # 依狀態過濾
    if not live_df.empty:
        if "LIVE" in status_filter_tab:
            live_df = live_df[live_df["status"] == "LIVE"]
        elif "即將開賽" in status_filter_tab:
            live_df = live_df[live_df["status"] == "UPCOMING"]
        elif "已完賽" in status_filter_tab:
            live_df = live_df[live_df["status"] == "FINISHED"]

    # 顯示即時自動同步時間戳記狀態列
    tw_now_display = config.get_taiwan_now_str("%Y-%m-%d %H:%M:%S")
    st.markdown(f"""
    <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 6px; padding: 7px 14px; font-size: 12.5px; color: #10B981; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>⚡ <b>即時數據已就緒</b>：目前顯示「<b>{league_filter_tab}</b>」最新 4 大來源即時盤口 (已在選單動作時自動更新)</div>
        <div style="color: #9CA3AF; font-size: 11.5px;">🕒 台灣時間：<span style="color:#F9FAFB; font-family:'JetBrains Mono';">{tw_now_display}</span> | 4 來源同步</div>
    </div>
    """, unsafe_allow_html=True)

    if not live_df.empty:
        # 即時狀態計數 Bar
        c_live = len(live_df[live_df["status"] == "LIVE"])
        c_up = len(live_df[live_df["status"] == "UPCOMING"])
        c_fin = len(live_df[live_df["status"] == "FINISHED"])
        
        st.markdown(f"""
        <div style="display:flex; gap:14px; margin-bottom:14px; font-size:13px;">
            <span style="color:#EF4444; font-weight:700;">🔴 場中進行中: {c_live} 場</span>
            <span style="color:#3B82F6; font-weight:700;">⏳ 即將開賽: {c_up} 場</span>
            <span style="color:#9CA3AF; font-weight:700;">🏁 今日已完賽: {c_fin} 場</span>
            <span style="color:#6B7280;">(共 {len(live_df)} 場賽事)</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 逐場渲染包含 4 大來源表格化比對之專業卡片
        for _, row in live_df.iterrows():
            m_status = row.get("status", "UPCOMING")
            fav_is_home = float(row["sb_home_odds"] or 0) <= float(row["sb_away_odds"] or 0)
            
            # 動態取得主客隊讓分線
            h_line = float(row["sb_h_handicap_line"] if "sb_h_handicap_line" in row and pd.notna(row["sb_h_handicap_line"]) else (-1.5 if fav_is_home else 1.5))
            a_line = float(row["sb_a_handicap_line"] if "sb_a_handicap_line" in row and pd.notna(row["sb_a_handicap_line"]) else (1.5 if fav_is_home else -1.5))
            
            is_esports = (row.get("sport") == "esports") or (row.get("league") in ["LCK", "LPL"])
            unit_label = "局" if is_esports else "分"

            # 依賽事生命週期狀態定制外觀
            if m_status == "LIVE":
                card_border = "#EF4444"
                status_html = f'<span class="status-badge-red" style="font-weight:700; background:rgba(239,68,68,0.2);">🔴 LIVE 場中滾球</span>'
                period_html = f'<span style="font-size: 13px; color: #F59E0B; font-weight: 700; margin-left: 8px;">📍 {row["live_period"]}</span>'
                score_display = f"""
                <div style="font-size: 20px; font-weight: 800; color: #F9FAFB; margin: 4px 0 8px 0;">
                    {row['home_team']} <span style="font-size:13px; color:#9CA3AF; font-weight:normal;">(主)</span> 
                    <span style="color:#10B981; font-size:24px; margin: 0 8px; font-family:'JetBrains Mono';">{row['live_score_home']} : {row['live_score_away']}</span> 
                    {row['away_team']} <span style="font-size:13px; color:#9CA3AF; font-weight:normal;">(客)</span>
                </div>
                """
            elif m_status == "FINISHED":
                card_border = "#4B5563"
                status_html = f'<span style="background:#374151; color:#9CA3AF; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600;">🏁 終場完賽 (Final)</span>'
                period_html = f'<span style="font-size: 12px; color: #9CA3AF; margin-left: 8px;">開賽時間：{row["start_time"]}</span>'
                score_display = f"""
                <div style="font-size: 16px; font-weight: 700; color: #E5E7EB; margin: 4px 0 8px 0;">
                    {row['home_team']} <span style="color:#9CA3AF; margin: 0 4px;">VS</span> {row['away_team']}
                    <div style="font-size:13px; color:#10B981; margin-top:2px;">🏆 {row['final_score']}</div>
                </div>
                """
            else:
                card_border = '#10B981' if fav_is_home else '#3B82F6'
                status_html = f'<span class="status-badge-blue">⏳ 賽前初盤</span>'
                period_html = f'<span style="font-size: 12px; color: #9CA3AF; margin-left: 8px;">🕒 開賽時間：{row["start_time"]} ({row["live_period"] if row["live_period"] else "即將開賽"})</span>'
                score_display = f"""
                <div style="font-size: 17px; font-weight: 700; color: #F9FAFB; margin: 4px 0 8px 0;">
                    {row['home_team']} <span style="font-size:12px; color:#9CA3AF; font-weight:normal;">(主)</span> 
                    <span style="color:#EF4444; margin: 0 6px;">VS</span> 
                    {row['away_team']} <span style="font-size:12px; color:#9CA3AF; font-weight:normal;">(客)</span>
                </div>
                """

            with st.container():
                st.markdown(f"""
                <div style="background: #111827; border: 1px solid #1F2937; border-left: 5px solid {card_border}; border-radius: 8px; padding: 14px 18px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div>
                            <span class="status-badge-blue">[{row['league']}]</span>
                            {status_html}
                            {period_html}
                        </div>
                        <div style="font-size: 11.5px; color: #9CA3AF;">
                            🔥 熱門方：<b style="color:{'#10B981' if fav_is_home else '#3B82F6'};">{row['favorite_team'] or (row['home_team'] if fav_is_home else row['away_team'])}</b>
                        </div>
                    </div>
                    {score_display}
                </div>
                """, unsafe_allow_html=True)
                
                # 取得該場賽事 4 大來源表格數據
                table_df = db.get_match_all_sources_table(row["match_id"])
                
                # 表格化列出 4 個來源
                st.markdown(f"##### 📋 4 大來源賠率表格化對照 (Sportsbet • Polymarket • Kalshi • Oddsportal)")
                
                # 提取最佳賠率
                valid_h_ml = [float(v) for v in table_df["主隊獨贏 (Home ML)"] if float(v) > 0]
                valid_a_ml = [float(v) for v in table_df["客隊獨贏 (Away ML)"] if float(v) > 0]
                best_h_ml = max(valid_h_ml) if valid_h_ml else 0.0
                best_a_ml = max(valid_a_ml) if valid_a_ml else 0.0
                
                best_h_source = table_df[table_df["主隊獨贏 (Home ML)"] == best_h_ml]["賠率來源 (Source)"].values[0] if valid_h_ml else ""
                best_a_source = table_df[table_df["客隊獨贏 (Away ML)"] == best_a_ml]["賠率來源 (Source)"].values[0] if valid_a_ml else ""

                # 呈現高雅金融風格 DataFrame
                display_cols = [
                    "賠率來源 (Source)", "市場類型", "主隊獨贏 (Home ML)", "客隊獨贏 (Away ML)",
                    "主隊隱含勝率", "客隊隱含勝率", "主隊讓分盤口", "客隊讓分盤口", "大小分 (Totals)", "抽水率/價差", "連線狀態"
                ]
                st.dataframe(
                    table_df[display_cols].style.format({
                        "主隊獨贏 (Home ML)": "{:.2f}",
                        "客隊獨贏 (Away ML)": "{:.2f}"
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                # 最佳下注路徑與套利/試算 Bar
                c_opt1, c_opt2, c_opt3 = st.columns([3.5, 3.5, 3])
                with c_opt1:
                    st.markdown(f"""
                    <div style="background: #131B2A; border: 1px solid #1F2937; border-radius: 6px; padding: 8px 12px; font-size: 12.5px;">
                        <span style="color:#9CA3AF;">⭐ 主隊最佳賠率：</span><b style="color:#10B981; font-size:14px;">{best_h_ml:.2f}</b> <span style="color:#60A5FA;">({best_h_source})</span><br>
                        <span style="color:#9CA3AF;">⭐ 客隊最佳賠率：</span><b style="color:#3B82F6; font-size:14px;">{best_a_ml:.2f}</b> <span style="color:#60A5FA;">({best_a_source})</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with c_opt2:
                    # 跨市場套利與價差檢驗
                    if best_h_ml > 1.0 and best_a_ml > 1.0:
                        combined_margin = (1.0 / best_h_ml) + (1.0 / best_a_ml)
                        if combined_margin < 1.0:
                            arb_gain = round(((1.0 / combined_margin) - 1.0) * 100, 2)
                            arb_html = f'<span style="color:#10B981; font-weight:700;">⚡ 發現無風險套利空間！保證報酬率 +{arb_gain}%</span>'
                        else:
                            spread_diff = round((combined_margin - 1.0) * 100, 2)
                            arb_html = f'<span style="color:#9CA3AF;">全市場最佳組合價差：<b style="color:#F9FAFB;">+{spread_diff}%</b> (極窄點差)</span>'
                    else:
                        arb_html = '<span style="color:#9CA3AF;">計算中...</span>'

                    st.markdown(f"""
                    <div style="background: #131B2A; border: 1px solid #1F2937; border-radius: 6px; padding: 8px 12px; font-size: 12.5px;">
                        <span style="color:#9CA3AF;">💡 跨市場價差狀態：</span><br>
                        {arb_html}
                    </div>
                    """, unsafe_allow_html=True)

                with c_opt3:
                    stake_test = 100.0
                    target_ret_h = round(stake_test * best_h_ml, 1) if best_h_ml > 0 else 0
                    target_ret_a = round(stake_test * best_a_ml, 1) if best_a_ml > 0 else 0
                    st.caption(f"💵 下注 $100 主隊最佳可得: **${target_ret_h}**")
                    st.caption(f"💵 下注 $100 客隊最佳可得: **${target_ret_a}**")

                st.divider()
    else:
        st.info(f"目前在「{league_filter_tab}」中無符合篩選條件之賽事。請切換上方下拉選單或調整狀態。")

# --------------------------------------------------
# TAB 2: 低賠讓分最佳投資區間分析
# --------------------------------------------------
with tab_fav:
    st.subheader("🎯 熱門強隊讓分 (-1.5) 最佳投資報酬率區間分析")
    st.caption("透過大數據回測熱門球隊在各個獨贏賠率區間中，讓分盤 (-1.5) 的實際過盤率與平均每注回報率 (ROI)，找出兼具高勝率與優渥賠率的黃金下注區間。")

    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        target_sport = st.selectbox(
            "選擇賽事項目",
            ["baseball", "esports"],
            format_func=lambda x: "⚾ 棒球 (MLB, NPB, CPBL)" if x == "baseball" else "🎮 電競 (LCK, LPL)"
        )
    with col_f2:
        available_leagues = ["全部聯盟"] + (["MLB", "NPB", "CPBL"] if target_sport == "baseball" else ["LCK", "LPL"])
        target_league_raw = st.selectbox("選擇聯盟分區", available_leagues, index=1)
        target_league = None if "全部" in target_league_raw else target_league_raw

    # 執行區間分析
    analysis_res = favorite_spread_analyzer.analyze_league(sport=target_sport, league=target_league)
    
    # 策略判定建議
    st.info(analysis_res["recommendation"])

    summary_df = pd.DataFrame(analysis_res["brackets_summary"])
    
    if not summary_df.empty and "bracket_label" in summary_df.columns:
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            fig_cover = px.bar(
                summary_df,
                x="bracket_label",
                y="cover_rate",
                color="roi_pct",
                color_continuous_scale=["#1F2937", "#3B82F6", "#10B981"],
                labels={"bracket_label": "獨贏賠率區間", "cover_rate": "讓分 (-1.5) 過盤率 (%)", "roi_pct": "ROI (%)"},
                title=f"【{target_league or target_sport.upper()}】各區間讓分過盤勝率 (%)",
                text="cover_rate"
            )
            fig_cover.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_cover.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#0B0F19",
                font=dict(color="#F3F4F6", family="Inter"),
                height=380,
                yaxis=dict(range=[0, 80], gridcolor="#1F2937")
            )
            st.plotly_chart(fig_cover, use_container_width=True)
            
        with col_c2:
            fig_roi = px.line(
                summary_df,
                x="bracket_label",
                y="roi_pct",
                markers=True,
                labels={"bracket_label": "獨贏賠率區間", "roi_pct": "每注投資回報率 ROI (%)"},
                title=f"【{target_league or target_sport.upper()}】各區間每注投資回報率 (ROI %)"
            )
            fig_roi.add_hline(y=0, line_dash="dash", line_color="#EF4444", annotation_text="損益平衡線 (0% ROI)")
            fig_roi.update_traces(line=dict(color='#10B981', width=3), marker=dict(size=8, color='#10B981'))
            fig_roi.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#0B0F19",
                font=dict(color="#F3F4F6", family="Inter"),
                height=380,
                yaxis=dict(gridcolor="#1F2937")
            )
            st.plotly_chart(fig_roi, use_container_width=True)

        # 詳細數據表格
        st.subheader("📋 各賠率區間詳細績效數據表")
        display_df = summary_df[[
            "bracket_label", "sample_size", "cover_count", "cover_rate",
            "avg_ml_odds", "avg_spread_odds", "roi_pct", "verdict"
        ]].copy()
        display_df.columns = [
            "獨贏賠率區間", "歷史樣本數", "讓分過盤場次", "讓分過盤率 (%)",
            "平均獨贏賠率", "平均讓分賠率", "投資回報率 ROI (%)", "量化策略建議"
        ]
        
        st.dataframe(
            display_df.style.map(
                lambda v: "color: #10B981; font-weight: bold;" if "+" in str(v) or "⭐️" in str(v) or "✅" in str(v) else ("color: #EF4444; font-weight: bold;" if "-" in str(v) or "❌" in str(v) else ""),
                subset=["投資回報率 ROI (%)", "量化策略建議"]
            ),
            use_container_width=True,
            hide_index=True
        )

    # 跨聯盟橫向比對
    st.subheader(f"🌐 {'棒球 (MLB vs NPB vs CPBL)' if target_sport == 'baseball' else '電競 (LCK vs LPL)'} 各聯盟甜蜜點橫向對比")
    comp_df = favorite_spread_analyzer.get_comparison_by_leagues(sport=target_sport)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

# --------------------------------------------------
# TAB 2: 即時盤口與變動監控
# --------------------------------------------------
with tab_live:
    st.subheader("📈 Sportsbet 即時盤口與市場水位監控")
    
    # 賠率跳水警報卡片
    if steam_alerts:
        st.warning(f"🚨 **偵測到 {len(steam_alerts)} 筆賠率急跌跳水（異常資金大單湧入）！**")
        alert_df = pd.DataFrame(steam_alerts)
        st.dataframe(
            alert_df[["league", "team", "side", "opponent", "open_odds", "current_odds", "drop_pct", "signal"]].rename(
                columns={
                    "league": "聯盟", "team": "跳水隊伍", "side": "主客",
                    "opponent": "對手", "open_odds": "初始賠率", "current_odds": "現盤賠率",
                    "drop_pct": "下跌幅度 (%)", "signal": "訊號"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("🟢 目前市場賠率走勢平穩，未出現劇烈單邊跳水。")

    st.subheader("🏟️ 今日即時賽事與盤口列表")
    live_df = db.get_live_matches_with_odds(sport=selected_sport, league=selected_league)
    
    if not live_df.empty:
        grid_data = []
        for _, row in live_df.iterrows():
            fav_is_home = float(row["sb_home_odds"] or 0) <= float(row["sb_away_odds"] or 0)
            h_line = float(row["sb_h_handicap_line"] if "sb_h_handicap_line" in row and pd.notna(row["sb_h_handicap_line"]) else (-1.5 if fav_is_home else 1.5))
            a_line = float(row["sb_a_handicap_line"] if "sb_a_handicap_line" in row and pd.notna(row["sb_a_handicap_line"]) else (1.5 if fav_is_home else -1.5))
            
            st_badge = "🔴 LIVE 場中" if row["status"] == "LIVE" else ("🏁 完賽" if row["status"] == "FINISHED" else "⏳ 賽前")
            period_str = row["live_period"] if row["status"] != "FINISHED" else row["final_score"]

            grid_data.append({
                "賽事狀態": st_badge,
                "聯盟": row["league"],
                "開賽時間 (台灣時間)": row["start_time"],
                "即時戰況/局數": period_str,
                "對戰組合": f"{row['home_team']} (主) vs {row['away_team']} (客)",
                "Sportsbet 獨贏": f"主: {row['sb_home_odds']} | 客: {row['sb_away_odds']}",
                "讓分盤口 (Spread)": f"{row['home_team'].split()[0]} ({h_line:+.1f}): {row['sb_h_spread_odds']} | {row['away_team'].split()[0]} ({a_line:+.1f}): {row['sb_a_spread_odds']}",
                "大小分 (Totals)": f"{row['sb_total_line']} (大: {row['sb_over_odds']} / 小: {row['sb_under_odds']})",
                "更新時間 (台灣時間)": row["odds_updated_at"]
            })
        st.dataframe(pd.DataFrame(grid_data), use_container_width=True, hide_index=True)
        
        # 單場折線圖
        st.subheader("📈 單場賽事賠率跳動歷史折線圖")
        selected_match_id = st.selectbox(
            "選擇比賽檢視走勢",
            options=live_df["match_id"].tolist(),
            format_func=lambda m_id: f"[{live_df[live_df['match_id']==m_id]['league'].values[0]}] {live_df[live_df['match_id']==m_id]['home_team'].values[0]} vs {live_df[live_df['match_id']==m_id]['away_team'].values[0]}"
        )
        
        match_history = movement_analyzer.get_odds_movement_chart_data(selected_match_id)
        if not match_history.empty:
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(x=match_history["timestamp"], y=match_history["home_odds"], mode="lines+markers", name="主隊獨贏賠率 (Home ML)", line=dict(color="#3B82F6", width=2.5)))
            fig_hist.add_trace(go.Scatter(x=match_history["timestamp"], y=match_history["away_odds"], mode="lines+markers", name="客隊獨贏賠率 (Away ML)", line=dict(color="#F59E0B", width=2.5)))
            fig_hist.add_trace(go.Scatter(x=match_history["timestamp"], y=match_history["handicap_home_odds"], mode="lines+markers", name="主隊讓分 (-1.5) 賠率", line=dict(color="#10B981", width=2.5, dash="dash")))
            fig_hist.update_layout(
                title="Sportsbet 賠率歷史跳動走勢",
                paper_bgcolor="#111827",
                plot_bgcolor="#0B0F19",
                font=dict(color="#F3F4F6", family="Inter"),
                xaxis_title="時間 (台灣時間 UTC+8)",
                yaxis_title="賠率 (Decimal)",
                height=400,
                yaxis=dict(gridcolor="#1F2937"),
                xaxis=dict(gridcolor="#1F2937")
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("該場比賽尚無多次跳動歷史。")
    else:
        st.info("目前無符合篩選條件之即時賽事。")

# --------------------------------------------------
# TAB 3: 跨平台套利與 +EV 專區
# --------------------------------------------------
with tab_ev:
    st.subheader("⚡ 跨平台套利 (Surebet) 與 +EV 價值投注專區")
    
    st.markdown("#### 1. ⚡ 4 大來源跨平台無風險套利掃描 (Surebet)")
    st.caption("全方位比對 澳洲 Sportsbet、Polymarket 預測市場、Kalshi CFTC 合約 與 Oddsportal 全球共識 之跨平台價差，鎖定 100% 無風險利潤。")
    
    bankroll_input = st.number_input("設定套利總本金 ($)", min_value=100.0, max_value=100000.0, value=1000.0, step=100.0)
    arb_results = arbitrage_scanner.scan_arbitrage_opportunities(total_bankroll=bankroll_input)
    
    if arb_results:
        st.success(f"🎉 發現 **{len(arb_results)}** 個 4 大來源即時無風險套利機會！")
        st.dataframe(
            pd.DataFrame(arb_results)[["league", "pair", "market", "side_a", "side_b", "roi_pct", "stake_a", "stake_b", "net_profit", "rating"]].rename(
                columns={
                    "league": "聯盟", "pair": "對沖平台組合", "market": "盤口類型", "side_a": "下注邊 A", "side_b": "下注邊 B",
                    "roi_pct": "套利回報率 (%)", "stake_a": "注碼 A", "stake_b": "注碼 B",
                    "net_profit": "預期保證淨利", "rating": "評級"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("目前 4 大市場賠率緊密，暫無顯著的無風險套利空間。")

    st.divider()

    st.markdown("#### 2. 💎 4 大來源正期望值價值投注 (+EV Scanner & Kelly Criterion)")
    st.caption("透過預測市場與全球博彩共識去除抽水 (De-vig) 算出公正真勝率，尋找 Sportsbet、Polymarket、Kalshi 盤口中的超額 +EV 數學期望值。")
    
    col_ev1, col_ev2 = st.columns(2)
    with col_ev1:
        min_ev_threshold = st.slider("最低期望值門檻 (+EV %)", min_value=-3.0, max_value=15.0, value=0.0, step=0.5)
    with col_ev2:
        kelly_frac = st.select_slider(
            "Kelly 資金管理比例 (Kelly Multiplier)",
            options=[0.1, 0.25, 0.5, 1.0],
            value=0.25,
            format_func=lambda x: f"{x}x (保守 1/4 Kelly)" if x==0.25 else (f"{x}x (超保守 1/10)" if x==0.1 else f"{x}x (積極)")
        )

    ev_results = ev_calculator.scan_positive_ev(min_ev_pct=min_ev_threshold, kelly_fraction=kelly_frac)
    if ev_results:
        st.dataframe(
            pd.DataFrame(ev_results)[["league", "source", "team", "side", "opponent", "odds", "fair_odds", "true_win_rate", "ev_pct", "kelly_stake_pct", "rating"]].rename(
                columns={
                    "league": "聯盟", "source": "推薦平台", "team": "推薦下注方", "side": "主客", "opponent": "對手",
                    "odds": "實時盤口賠率", "fair_odds": "市場公正真賠率",
                    "true_win_rate": "客觀勝率", "ev_pct": "期望值 (+EV %)",
                    "kelly_stake_pct": "建議 Kelly 注碼比", "rating": "評級"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("目前在此門檻下暫無 +EV 價值投注機會（可將上方門檻滑桿調至 0% 查看所有接近損益平衡的賽事）。")

# --------------------------------------------------
# TAB 4: 策略歷史回測與模擬器
# --------------------------------------------------
with tab_backtest:
    st.subheader("🧪 策略歷史數據回測與資產損益模擬 (Backtesting Engine)")
    st.caption("設定特定賠率區間與注碼策略，模擬在歷史數千場賽事中的累積損益曲線、勝率與最大回撤。")

    with st.expander("🛠️ 設定回測參數", expanded=True):
        c_b1, c_b2, c_b3 = st.columns(3)
        with c_b1:
            bt_sport = st.selectbox("選擇運動項目", ["baseball", "esports"], key="bt_sport", format_func=lambda x: "⚾ 棒球" if x=="baseball" else "🎮 電競")
            bt_leagues = ["全部聯盟"] + (["MLB", "NPB", "CPBL"] if bt_sport=="baseball" else ["LCK", "LPL"])
            bt_league_raw = st.selectbox("選擇聯盟", bt_leagues, key="bt_league")
            bt_league = None if "全部" in bt_league_raw else bt_league_raw
        with c_b2:
            bt_market = st.selectbox(
                "盤口策略模式",
                options=["SPREAD_FAVORITE", "ML_FAVORITE", "SPREAD_UNDERDOG"],
                format_func=lambda x: "⭐️ 熱門強隊讓分 (-1.5 Spread)" if x=="SPREAD_FAVORITE" else ("熱門強隊獨贏 (Moneyline)" if x=="ML_FAVORITE" else "弱隊受讓 (+1.5 Spread)")
            )
            bt_stake_mode = st.radio("注碼管理", ["FLAT", "PERCENT"], format_func=lambda x: "固定注碼 ($100)" if x=="FLAT" else "本金比例 (2% of Bankroll)", horizontal=True)
        with c_b3:
            bt_init_bank = st.number_input("起始本金 ($)", value=10000.0, step=1000.0)
            bt_ml_range = st.slider("熱門隊獨贏賠率範圍", min_value=1.05, max_value=2.20, value=(1.20, 1.50), step=0.05)

    if st.button("🚀 執行歷史策略回測", type="primary", use_container_width=True):
        with st.spinner("正在模擬數千場歷史賽事並計算資產淨值曲線..."):
            bt_res = backtester.run_backtest(
                sport=bt_sport,
                league=bt_league,
                market_mode=bt_market,
                min_ml_odds=bt_ml_range[0],
                max_ml_odds=bt_ml_range[1],
                initial_bankroll=bt_init_bank,
                stake_mode=bt_stake_mode,
                stake_unit=100.0 if bt_stake_mode=="FLAT" else 2.0
            )

        if "error" in bt_res:
            st.error(bt_res["error"])
        else:
            k1, k2, k3, k4, k5, k6 = st.columns(6)
            k1.metric("總下注場次", f"{bt_res['total_bets']} 場")
            k2.metric("勝率", f"{bt_res['win_rate_pct']}%", f"{bt_res['wins']}W {bt_res['losses']}L")
            k3.metric("最終資產", f"${bt_res['final_bankroll']}", f"{'+' if bt_res['total_net_profit']>=0 else ''}${bt_res['total_net_profit']}")
            k4.metric("投資回報率 ROI", f"{'+' if bt_res['roi_pct']>=0 else ''}{bt_res['roi_pct']}%")
            k5.metric("最大回撤", f"{bt_res['max_drawdown_pct']}%", delta_color="inverse")
            k6.metric("獲利因子", f"{bt_res['profit_factor']}")

            # 資產曲線
            st.subheader("📈 策略累積資產成長曲線 (Equity Curve)")
            fig_pnl = px.line(
                x=bt_res["equity_dates"],
                y=bt_res["equity_curve"],
                labels={"x": "賽事日期", "y": "帳戶總資產 ($)"},
                title=f"資產淨值成長曲線 (起始: ${bt_init_bank} -> 最終: ${bt_res['final_bankroll']})"
            )
            fig_pnl.add_hline(y=bt_init_bank, line_dash="dash", line_color="#9CA3AF", annotation_text="起始本金線")
            fig_pnl.update_traces(line=dict(color="#10B981" if bt_res["total_net_profit"]>=0 else "#EF4444", width=2.5))
            fig_pnl.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#0B0F19",
                font=dict(color="#F3F4F6", family="Inter"),
                height=420,
                yaxis=dict(gridcolor="#1F2937"),
                xaxis=dict(gridcolor="#1F2937")
            )
            st.plotly_chart(fig_pnl, use_container_width=True)

# --------------------------------------------------
# TAB 5: 系統與資料庫管理
# --------------------------------------------------
with tab_db:
    st.subheader("⚙️ 系統資料庫維護與同步管理")
    
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        st.markdown("#### 📦 重新導入歷史數據庫")
        st.caption("重新產生涵蓋 MLB, NPB, CPBL, LCK, LPL 數千場真實歷史賽事的資料庫種子。")
        if st.button("🔄 重構歷史資料庫"):
            with st.spinner("正在重構資料庫..."):
                init_seed_database(force_reload=True)
                st.success("歷史資料庫重構完成！")
                st.rerun()
                
    with c_m2:
        st.markdown("#### 🌐 即時爬蟲全量同步")
        st.caption("手動觸發 Sportsbet 與 Oddsportal 即時盤口更新。")
        if st.button("🚀 執行全量爬取同步"):
            with st.spinner("同步中..."):
                res = sync_service.sync_once()
                st.success(f"同步完成！已獲取 {res['sportsbet_events']} 場賽事實時數據")
                st.rerun()

    st.divider()

    st.divider()
    st.subheader("📑 最近 50 場歷史賽事記錄")
    hist_sample = db.get_historical_matches()
    st.dataframe(hist_sample.head(50), use_container_width=True, hide_index=True)

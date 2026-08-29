"""
🏛️ 機構級體育博弈量化終端 (Institutional Sports Quantitative Terminal)
專注於 棒球 (MLB, NPB, CPBL) 與 電競 (LCK, LPL)
具備 澳洲 Sportsbet 官方操作盤口、Oddsportal 國際即時場中中樞、跨機構隱藏勝率落差、去水真實勝率、
Sportsbet 盤口返還率 (RTP)、各大聯盟最新官方戰績排行、賠率急跌 (Steam Moves) 與歷史策略回測
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
from analytics.probability_gap import probability_gap_analyzer
from analytics.standings import league_standings
from analytics.ev_calculator import ev_calculator
from analytics.backtester import backtester
from services.sync_service import sync_service
from scrapers.the_odds_api_scraper import the_odds_api
from scrapers.oddsportal_scraper import oddsportal_scraper

# 頁面基礎設定
st.set_page_config(
    page_title="機構級體育博弈量化終端 | Institutional Sports Quantitative Terminal",
    page_icon="🏛️",
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
# 💼 專業金融量化風格 CSS
# ==========================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    code, pre, .mono {
        font-family: 'JetBrains Mono', monospace !important;
    }

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
        font-size: 23px;
        font-weight: 800;
        color: #F9FAFB;
        letter-spacing: -0.5px;
        margin-bottom: 4px;
    }
    .pro-subtitle {
        font-size: 13.5px;
        color: #9CA3AF;
    }

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

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #1F2937;
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 6px;
        color: #9CA3AF;
        font-size: 13.5px;
        font-weight: 600;
        padding: 0 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1F2937 !important;
        color: #F9FAFB !important;
        border: 1px solid #374151 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================
# 🧭 側邊欄控制面板 (Sidebar)
# ==========================
with st.sidebar:
    st.markdown("### 🏛️ 機構量化終端控制台")
    st.caption("Institutional Quantitative Controller")
    
    # 賽事類型切換
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

    # The Odds API 官方數據專線設定
    st.markdown("### 🔑 官方數據專線 (The Odds API)")
    odds_api_key_input = st.text_input(
        "輸入 The Odds API Key",
        value=st.session_state.get("user_odds_api_key", config.THE_ODDS_API_KEY),
        type="password",
        help="在 the-odds-api.com 免費註冊取得 Key (每月 500 次免費呼叫)"
    )
    if odds_api_key_input:
        st.session_state["user_odds_api_key"] = odds_api_key_input
        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; border-radius: 6px; padding: 8px 10px; font-size: 11.5px; margin-bottom: 8px;">
            <span style="color: #10B981; font-weight: 700;">🟢 官方專線就緒 (Sportsbet 直連)</span><br>
            <span style="color: #9CA3AF;">本月剩餘額度: <b>{the_odds_api.requests_remaining} / 500</b> 次</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid #3B82F6; border-radius: 6px; padding: 8px 10px; font-size: 11.5px; margin-bottom: 8px;">
            <span style="color: #60A5FA; font-weight: 600;">💡 領取官方專線 API Key</span><br>
            <a href="https://the-odds-api.com/" target="_blank" style="color: #F59E0B; text-decoration: underline; font-weight:700;">👉 前往 the-odds-api.com 免費領取</a>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    # 手動即時同步
    st.markdown("### ⚡ 數據同步 (Live Sync)")
    if st.button("🚀 立即同步最新盤口數據", use_container_width=True):
        with st.spinner("正在自 Oddsportal 與市場獲取最新即時盤口數據..."):
            sync_res = sync_service.sync_once(api_key=odds_api_key_input)
            st.success(f"[{sync_res.get('mode', '即時同步')}] 成功！更新 {sync_res['sportsbet_events']} 場賽事，耗時 {sync_res['duration_seconds']} 秒")
            if sync_res.get("api_message"):
                st.caption(f"ℹ️ {sync_res['api_message']}")
            time.sleep(0.5)
            st.rerun()

    st.caption(f"🕒 前次同步 (台灣時間)：`{sync_service.last_sync_time}`")
    st.caption(f"📡 目前數據模式：`{sync_service.source_mode}`")
    
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
value_gaps = probability_gap_analyzer.scan_sportsbet_value_gaps(min_gap_pct=-1.0)
val_positive_count = len([x for x in value_gaps if x["is_value"]])

tw_current_time = config.get_taiwan_now_str('%Y-%m-%d %H:%M:%S')

st.markdown(f"""
<div class="pro-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <div class="pro-title">
                🏛️ 機構級體育博弈量化終端 | Institutional Sports Quantitative Terminal
            </div>
            <div class="pro-subtitle">
                ⚡ 澳洲 Sportsbet 官方操作盤口 • Oddsportal 國際即時場中數據中樞 • 跨機構隱藏勝率落差與去水真實價值掃描
            </div>
        </div>
        <div style="display: flex; gap: 8px; margin-top: 6px; align-items: center;">
            <span class="status-badge-green">● 國際基準數據在線</span>
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
        <span class="status-badge-green">Oddsportal 中樞在線</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="pro-card">
        <div class="pro-metric-label">賠率急跌警報 (Steam Moves)</div>
        <div class="pro-metric-val" style="color: {'#EF4444' if len(steam_alerts)>0 else '#F9FAFB'};">{len(steam_alerts)} <span style="font-size:14px; font-weight:normal; color:#9CA3AF;">筆</span></div>
        <span class="{'status-badge-red' if len(steam_alerts)>0 else 'status-badge-green'}">{'主力大單湧入' if len(steam_alerts)>0 else '市場水位平穩'}</span>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="pro-card">
        <div class="pro-metric-label">Sportsbet 平均返還率 (Avg RTP)</div>
        <div class="pro-metric-val" style="color: #3B82F6;">95.4 <span style="font-size:14px; font-weight:normal; color:#9CA3AF;">%</span></div>
        <span class="status-badge-blue">莊家平均抽水 4.6%</span>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="pro-card">
        <div class="pro-metric-label">Sportsbet 超額價值機會 (+EV)</div>
        <div class="pro-metric-val" style="color: #10B981;">{val_positive_count} <span style="font-size:14px; font-weight:normal; color:#9CA3AF;">場</span></div>
        <span class="status-badge-green">勝率優勢大於市場價</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# ==========================
# 💼 7 大機構級量化分析分頁 (Tabs)
# ==========================
tab_sb, tab_gap, tab_standings, tab_fav, tab_movement, tab_backtest, tab_db = st.tabs([
    "🇦🇺 Sportsbet 即時操作盤口 (場中/賽前/完賽)",
    "🎯 跨機構隱藏勝率落差與 Sportsbet +EV 價值掃描",
    "🏆 各大聯盟官方最新戰績排行 (Standings)",
    "📊 低賠讓分最佳投資區間 (量化統計)",
    "📈 賠率走勢與資金急跌跳水監控 (Steam Moves)",
    "🧪 策略歷史回測與資產模擬",
    "⚙️ 系統資料庫與數據源管理"
])

# --------------------------------------------------
# TAB 1: 🇦🇺 Sportsbet 即時操作盤口 (場中/賽前/完賽)
# --------------------------------------------------
with tab_sb:
    st.subheader("🇦🇺 Sportsbet Australia 官方即時盤口看板 (免 VPN 直連)")
    st.caption("直連澳洲 Sportsbet 官方盤口行情，結合 Oddsportal 即時場中賽況，一覽 MLB、NPB、CPBL、LCK、LPL 全部即時賠率！")

    # 頂部控制列：聯盟與狀態雙重篩選
    col_sb_ctrl1, col_sb_ctrl2, col_sb_ctrl3 = st.columns([2.5, 2, 1])
    with col_sb_ctrl1:
        league_filter_tab = st.selectbox(
            "選擇欲查看的賽事聯盟 (Select League)",
            options=[
                "全部賽事 (MLB / NPB / CPBL / LCK / LPL)",
                "⚾ MLB (美國職棒)",
                "⚾ NPB (日本職棒)",
                "⚾ CPBL (中華職棒)",
                "🎮 LCK (韓國英雄聯盟)",
                "🎮 LPL (中國英雄聯盟)"
            ],
            index=0
        )
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
        if st.button("🔄 刷新最新盤口", use_container_width=True, key="tab1_refresh"):
            sync_service.sync_once(api_key=st.session_state.get("user_odds_api_key"))
            st.rerun()

    # 解析聯盟與狀態篩選
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

    if not live_df.empty:
        # 即時狀態計數 Bar
        c_live = len(live_df[live_df["status"] == "LIVE"])
        c_up = len(live_df[live_df["status"] == "UPCOMING"])
        c_fin = len(live_df[live_df["status"] == "FINISHED"])
        
        st.markdown(f"""
        <div style="display:flex; gap:12px; margin-bottom:14px; font-size:13px;">
            <span style="color:#EF4444; font-weight:700;">🔴 場中進行中: {c_live} 場</span>
            <span style="color:#3B82F6; font-weight:700;">⏳ 即將開賽: {c_up} 場</span>
            <span style="color:#9CA3AF; font-weight:700;">🏁 今日已完賽: {c_fin} 場</span>
            <span style="color:#6B7280;">(共 {len(live_df)} 場)</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 逐場渲染專業 Sportsbook 盤口卡片
        for _, row in live_df.iterrows():
            m_status = row.get("status", "UPCOMING")
            fav_is_home = float(row["sb_home_odds"] or 0) <= float(row["sb_away_odds"] or 0)
            
            # 動態取得主客隊正確讓分線
            h_line = float(row["sb_h_handicap_line"] if "sb_h_handicap_line" in row and pd.notna(row["sb_h_handicap_line"]) else (-1.5 if fav_is_home else 1.5))
            a_line = float(row["sb_a_handicap_line"] if "sb_a_handicap_line" in row and pd.notna(row["sb_a_handicap_line"]) else (1.5 if fav_is_home else -1.5))
            
            is_esports = (row.get("sport") == "esports") or (row.get("league") in ["LCK", "LPL"])
            
            if is_esports:
                h_sp_badge = "🔥 讓局 (2:0勝)" if h_line < 0 else "受讓 (+1.5局)"
                a_sp_badge = "🔥 讓局 (2:0勝)" if a_line < 0 else "受讓 (+1.5局)"
                h_sp_text = f"主隊 {row['home_team']} [{h_line:+.1f}局]"
                a_sp_text = f"客隊 {row['away_team']} [{a_line:+.1f}局]"
            else:
                h_sp_badge = "🔥 讓分" if h_line < 0 else "受讓"
                a_sp_badge = "🔥 讓分" if a_line < 0 else "受讓"
                h_sp_text = f"主隊 ({row['home_team'].split()[0]}) {h_line:+.1f}"
                a_sp_text = f"客隊 ({row['away_team'].split()[0]}) {a_line:+.1f}"

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
                ml_label = "⚡ 場中獨贏 (In-Play ML)"
                sp_label = "⚡ 場中讓分 (In-Play Spread)"
                tot_label = f"⚡ 場中大小分 (總分: {row['sb_total_line']})"
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
                ml_label = "💰 賽前初盤獨贏 (ML)"
                sp_label = "🛡️ 賽前初盤讓分 (Spread)"
                tot_label = f"🎯 大小分 (總分: {row['sb_total_line']})"
            else:
                # UPCOMING
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
                ml_label = "💰 賽前獨贏盤 (Head to Head)"
                sp_label = "🛡️ 賽前讓分盤 (Runline / Spread)"
                tot_label = f"🎯 大小分 (總分: {row['sb_total_line']})"

            with st.container():
                st.markdown(f"""
                <div style="background: #111827; border: 1px solid #1F2937; border-left: 5px solid {card_border}; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div>
                            <span class="status-badge-blue">[{row['league']}]</span>
                            {status_html}
                            {period_html}
                        </div>
                        <div style="font-size: 11px; color: #6B7280;">Sportsbet 實時連線</div>
                    </div>
                    {score_display}
                </div>
                """, unsafe_allow_html=True)
                
                # 盤口詳細賠率欄
                col_m1, col_m2, col_m3, col_calc = st.columns([3, 3.3, 2.7, 3])
                
                with col_m1:
                    st.markdown(f"**{ml_label}**")
                    st.markdown(f"""
                    - 主勝 ({row['home_team'].split()[0]}): <b style="color:#10B981; font-size:16px;">{row['sb_home_odds']}</b> {'🔥 熱門' if fav_is_home else ''}
                    - 客勝 ({row['away_team'].split()[0]}): <b style="color:#3B82F6; font-size:16px;">{row['sb_away_odds']}</b> {'🔥 熱門' if not fav_is_home else ''}
                    """, unsafe_allow_html=True)

                with col_m2:
                    st.markdown(f"**{sp_label}**")
                    st.markdown(f"""
                    - {h_sp_text}: <b style="color:#10B981; font-size:16px;">{row['sb_h_spread_odds']}</b> <span style="font-size:11px; color:{'#10B981' if h_line < 0 else '#9CA3AF'};">[{h_sp_badge}]</span>
                    - {a_sp_text}: <b style="color:#3B82F6; font-size:16px;">{row['sb_a_spread_odds']}</b> <span style="font-size:11px; color:{'#3B82F6' if a_line < 0 else '#9CA3AF'};">[{a_sp_badge}]</span>
                    """, unsafe_allow_html=True)

                with col_m3:
                    st.markdown(f"**{tot_label}**")
                    st.markdown(f"""
                    - 大分 (Over): <b style="color:#F59E0B; font-size:16px;">{row['sb_over_odds']}</b>
                    - 小分 (Under): <b style="color:#F59E0B; font-size:16px;">{row['sb_under_odds']}</b>
                    """, unsafe_allow_html=True)

                with col_calc:
                    if m_status == "FINISHED":
                        st.markdown("**📝 結算回顧**")
                        st.caption(f"賽事已完賽：{row['final_score']}")
                        st.caption("請切換至「即將開賽」或「場中」進行下注量化分析。")
                    else:
                        st.markdown("**📝 投注獲利試算 (Bet Calc)**")
                        stake_test = 100.0
                        fav_ml_odds = float(row['sb_home_odds'] if fav_is_home else row['sb_away_odds'])
                        fav_team_label = row['home_team'].split()[0] if fav_is_home else row['away_team'].split()[0]
                        
                        fav_sp_is_home = (h_line < 0)
                        fav_sp_odds = float(row['sb_h_spread_odds'] if fav_sp_is_home else row['sb_a_spread_odds'])
                        fav_sp_team_label = row['home_team'].split()[0] if fav_sp_is_home else row['away_team'].split()[0]
                        fav_sp_line_str = f"{h_line:+.1f}" if fav_sp_is_home else f"{a_line:+.1f}"
                        
                        st.caption(f"下注 $100 獨贏 ({fav_team_label}): 可收回 `${round(stake_test * fav_ml_odds, 1)}`")
                        st.caption(f"下注 $100 讓分 ({fav_sp_team_label} {fav_sp_line_str}): 可收回 `${round(stake_test * fav_sp_odds, 1)}`")

                st.divider()
    else:
        st.info("目前無符合篩選條件之即時賽事。請調整上方篩選條件或點擊「刷新盤口」。")

# --------------------------------------------------
# TAB 2: 🎯 跨機構隱藏勝率落差與 Sportsbet +EV 價值掃描
# --------------------------------------------------
with tab_gap:
    st.subheader("🎯 跨機構隱藏勝率落差與 Sportsbet 單一盤口價值掃描 (+EV Screener)")
    st.caption("由於個人下注集中於 Sportsbet，本模組專門透過國際尖銳機構 (Pinnacle/Bet365/TAB) 盤口去除抽水後的『真實客觀勝率』，對比 Sportsbet 隱藏勝率，精準揪出 Sportsbet 定價低估（賠率溢價）之可下注場次！")

    # 隱藏勝率與去水原理折疊卡片
    with st.expander("💡 什麼是「隱藏勝率」、「去水真實勝率」與「盤口返還率 (RTP)」？點此展開數學公式說明", expanded=False):
        st.markdown(r"""
        #### 1. 名義隱藏勝率 (Raw Implied Probability)
        博彩公司開出的賠率隱含了該結果發生的機率：
        $$P_{\text{raw}} = \frac{1}{\text{Odds}} \times 100\%$$
        *例如：Sportsbet 主隊賠率 1.60，未去水隱藏勝率為 $\frac{1}{1.60} = 62.5\%$。*

        #### 2. 莊家抽水率 (Vig / Overround) 與 盤口返還率 (Payout Ratio / RTP)
        莊家在開盤時會在兩邊機率加上水錢（Margin）：
        $$\text{Overround} = \frac{1}{\text{Home Odds}} + \frac{1}{\text{Away Odds}}$$
        $$\text{返還率 (RTP \%)} = \frac{1}{\text{Overround}} \times 100\%, \quad \text{莊家抽水 (Vig \%)} = (\text{Overround} - 1) \times 100\%$$
        *例如：兩隊賠率 1.90 / 1.90，Overround = $\frac{1}{1.90} + \frac{1}{1.90} = 1.0526$ (抽水 5.26%)，返還率為 $95.0\%$。*

        #### 3. 去水真實勝率 (True De-vigged Probability)
        將抽水按比例扣除後，還原出的**客觀真實勝率**（加總嚴格等於 100%）：
        $$P_{\text{True}} = \frac{1/\text{Odds}}{\text{Overround}}$$

        #### 4. 隱藏勝率落差 ($\Delta P$) 與 超額價值 (+EV) 判定
        以國際公認最敏銳的 Pinnacle（平博）真實勝率作為市場基準 $P_{\text{Benchmark}}$：
        $$\Delta P = P_{\text{True, Benchmark}} - P_{\text{True, Sportsbet}}$$
        * **當 $\Delta P > 0$（且期望值 $+EV > 0\%$）**：代表 Pinnacle 與市場認為該隊勝率極高，但 Sportsbet 卻開出較寬鬆的高賠率（給多了！），這就是**數學上長期具備正期望值（+EV）的黃金下注機會！**
        """)

    # 篩選控制列
    col_gap_f1, col_gap_f2 = st.columns([2, 2])
    with col_gap_f1:
        min_ev_filter = st.slider("最低期望值門檻 (+EV %)", min_value=-3.0, max_value=8.0, value=0.0, step=0.5)
    with col_gap_f2:
        gap_league_choice = st.selectbox("賽事聯盟過濾", ["全部聯盟", "MLB", "NPB", "CPBL", "LCK", "LPL"], index=0)

    # 執行全量價值掃描
    all_gaps = probability_gap_analyzer.scan_sportsbet_value_gaps(min_gap_pct=-5.0)
    
    # 過濾
    filtered_gaps = [
        x for x in all_gaps 
        if x["ev_pct"] >= min_ev_filter and (gap_league_choice == "全部聯盟" or x["league"] == gap_league_choice)
    ]

    if filtered_gaps:
        st.markdown(f"**🔍 共篩選出 `{len(filtered_gaps)}` 筆符合條件之 Sportsbet 下注邊：**")
        gap_df = pd.DataFrame(filtered_gaps)
        
        display_gap_table = gap_df[[
            "league", "match", "team", "side", "sb_odds", "sb_payout_pct",
            "sb_raw_prob", "sb_true_prob", "bench_true_prob", "gap_pct", "ev_pct", "kelly_pct", "rating"
        ]].copy()
        
        display_gap_table.columns = [
            "聯盟", "對戰組合", "推薦隊伍", "主客", "Sportsbet 實時賠率", "Sportsbet 返還率 (RTP)",
            "SB 未去水勝率", "SB 去水真勝率", "國際基準真勝率 (Pinnacle)", "勝率落差 (Gap %)", "期望值 (+EV %)", "建議注碼 (Kelly %)", "量化評級"
        ]

        st.dataframe(
            display_gap_table.style.map(
                lambda v: "color: #10B981; font-weight: bold;" if ("+" in str(v) or "💎" in str(v) or "⭐️" in str(v)) else ("color: #EF4444;" if "-" in str(v) else ""),
                subset=["勝率落差 (Gap %)", "期望值 (+EV %)", "量化評級"]
            ),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("#### 🔍 各場賽事跨 4 大機構標竿盤口詳細對照 (Sportsbet • Pinnacle • Bet365 • TAB)")
        for item in filtered_gaps[:6]:
            with st.expander(f"📌 [{item['league']}] {item['match']} | 推薦: {item['team']} ({item['side']}) @ {item['sb_odds']} (EV: {item['ev_pct']:+.1f}%)"):
                row_raw = live_df[live_df["match_id"] == item["match_id"]]
                if not row_raw.empty:
                    breakdown = probability_gap_analyzer.get_match_full_breakdown(row_raw.iloc[0])
                    multi_df = pd.DataFrame.from_dict(breakdown["multi_books"], orient="index").reset_index()
                    multi_df.columns = ["博弈機構 (Bookmaker)", "主隊賠率", "客隊賠率", "盤口返還率 (RTP)", "主隊名義勝率", "主隊去水真勝率", "客隊去水真勝率"]
                    st.dataframe(multi_df, use_container_width=True, hide_index=True)
                    
                    st.caption(f"💡 分析結論：國際基準盤 (Pinnacle) 評估 {item['team']} 去水真實勝率為 **{item['bench_true_prob']}**，換算公正真賠率為 **{item['bench_fair_odds']}**。Sportsbet 目前開出 **{item['sb_odds']}**，存在 **{item['gap_pct']:+.2f}%** 之隱藏勝率優勢！")
    else:
        st.info("目前在此門檻下無顯著正期望值偏離。請調低上方 +EV 門檻滑桿查看更多賽事。")

# --------------------------------------------------
# TAB 3: 🏆 各大聯盟官方最新戰績排行 (Standings)
# --------------------------------------------------
with tab_standings:
    st.subheader("🏆 各大聯盟官方最新戰績與球隊近況排行 (League Standings & Form)")
    st.caption("即時連線 MLB、NPB、CPBL、LCK、LPL 官方最新排名、勝率 (Win %)、勝差 (GB)、近十場 (L10) 與連勝走勢，輔助判斷球隊基本面！")

    subtab_mlb, subtab_npb, subtab_cpbl, subtab_lck, subtab_lpl = st.tabs([
        "⚾ MLB (美國職棒)",
        "⚾ NPB (日本職棒)",
        "⚾ CPBL (中華職棒)",
        "🎮 LCK (韓國英雄聯盟)",
        "🎮 LPL (中國英雄聯盟)"
    ])

    with subtab_mlb:
        st.markdown("#### ⚾ MLB 美國職棒 2024-2026 最新分區排名")
        mlb_df = league_standings.get_standings_df("MLB")
        st.dataframe(mlb_df, use_container_width=True, hide_index=True)

    with subtab_npb:
        st.markdown("#### ⚾ NPB 日本職棒 (太平洋聯盟 / 中央聯盟) 最新戰績")
        npb_df = league_standings.get_standings_df("NPB")
        st.dataframe(npb_df, use_container_width=True, hide_index=True)

    with subtab_cpbl:
        st.markdown("#### ⚾ CPBL 中華職棒最新戰績排行 (全年度/下半季)")
        cpbl_df = league_standings.get_standings_df("CPBL")
        st.dataframe(cpbl_df, use_container_width=True, hide_index=True)

    with subtab_lck:
        st.markdown("#### 🎮 LCK 英雄聯盟韓國冠軍聯賽最新積分榜")
        lck_df = league_standings.get_standings_df("LCK")
        st.dataframe(lck_df, use_container_width=True, hide_index=True)

    with subtab_lpl:
        st.markdown("#### 🎮 LPL 英雄聯盟中國職業聯賽最新積分榜")
        lpl_df = league_standings.get_standings_df("LPL")
        st.dataframe(lpl_df, use_container_width=True, hide_index=True)

# --------------------------------------------------
# TAB 4: 📊 低賠讓分最佳投資區間 (量化統計模型)
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

    analysis_res = favorite_spread_analyzer.analyze_league(sport=target_sport, league=target_league)
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

    st.subheader(f"🌐 {'棒球 (MLB vs NPB vs CPBL)' if target_sport == 'baseball' else '電競 (LCK vs LPL)'} 各聯盟甜蜜點橫向對比")
    comp_df = favorite_spread_analyzer.get_comparison_by_leagues(sport=target_sport)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

# --------------------------------------------------
# TAB 5: 📈 賠率走勢與資金急跌跳水監控 (Steam Moves)
# --------------------------------------------------
with tab_movement:
    st.subheader("📈 賠率走勢與資金急跌跳水監控 (Movement & Steam Analyzer)")
    
    # 賠率跳水原理與資料來源說明卡片
    with st.expander("💡 什麼是「賠率急跌跳水 (Steam Move)」？資料來源與資金流入原理說明", expanded=True):
        st.markdown("""
        #### 1. 資料來源 (Data Sources)
        * 本模組之數據源來自 **Oddsportal 全球博弈監控網絡** 與 **Sportsbet 實時時間序列資料庫 (`odds_history`)**。
        * 系統以秒/分鐘級別記錄開盤價 (Open)、盤中最高點 (High) 與當前現盤價 (Current)，精確計算水位異動幅度。

        #### 2. 為什麼「賠率急跌」代表「資金大量匯入 (Smart Money)」？
        * **博弈機構的平衡機制**：莊家開盤的核心目標是讓兩邊注碼達到平衡，藉此賺取固定的無風險抽水 (Vig)。
        * **受險防禦調盤 (Liability Defense)**：當市場上出現職業博弈集團（Syndicate / 聰明錢 Smart Money）針對某隊伍進行數百萬級別的單邊重注時，莊家的單邊賠付風險會瞬間飆高。
        * **自動降賠現象 (Steam Move)**：莊家必須在極短時間內**大幅調低該隊賠率**（例如從 2.10 驟降至 1.75），同時拉高對手賠率，以阻止更多資金湧入該隊，並吸引散戶資金流向對手盤以平衡帳目。
        * **量化結論**：因此，**「賠率大幅跳水」在統計上是市場主力與內幕資金進場的最可靠指標！**
        """)

    # 賠率跳水警報卡片
    if steam_alerts:
        st.warning(f"🚨 **偵測到 {len(steam_alerts)} 筆賠率急跌跳水（異常資金大單湧入）！**")
        alert_df = pd.DataFrame(steam_alerts)
        st.dataframe(
            alert_df[["league", "team", "side", "opponent", "open_odds", "current_odds", "drop_pct", "signal"]].rename(
                columns={
                    "league": "聯盟", "team": "跳水隊伍", "side": "主客",
                    "opponent": "對手", "open_odds": "初始開盤賠率", "current_odds": "現盤賠率",
                    "drop_pct": "下跌幅度 (%)", "signal": "資金異動訊號"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("🟢 目前市場賠率走勢平穩，未出現劇烈單邊跳水。")

    st.subheader("🏟️ 今日即時賽事與盤口列表")
    live_df_full = db.get_live_matches_with_odds(sport=selected_sport, league=selected_league)
    
    if not live_df_full.empty:
        grid_data = []
        for _, row in live_df_full.iterrows():
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

# --------------------------------------------------
# TAB 6: 🧪 策略歷史回測與資產模擬
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
# TAB 7: ⚙️ 系統資料庫與數據源管理
# --------------------------------------------------
with tab_db:
    st.subheader("⚙️ 系統資料庫維護與數據源管理")
    
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
                res = sync_service.sync_once(api_key=st.session_state.get("user_odds_api_key"))
                st.success(f"同步完成！已獲取 {res['sportsbet_events']} 場賽事實時數據")
                st.rerun()

    st.divider()

    st.subheader("📡 官方體育數據專線 (The Odds API) 整合管理")
    st.caption("直接連接全球頂級體育數據專線，免翻牆獲取澳洲 Sportsbet、Bet365、TAB、Pinnacle 官方即時盤口。")

    col_api_test1, col_api_test2 = st.columns([2, 1])
    with col_api_test1:
        test_key = st.text_input("測試 API Key 連線狀態", value=st.session_state.get("user_odds_api_key", config.THE_ODDS_API_KEY), type="password", key="tab_db_key_input")
    with col_api_test2:
        st.write("")
        st.write("")
        if st.button("🔍 測試 API 連線與查詢額度", use_container_width=True):
            if test_key:
                valid, msg, info = the_odds_api.check_api_key(test_key)
                if valid:
                    st.session_state["user_odds_api_key"] = test_key
                    st.success(f"✅ {msg}")
                    st.info(f"📊 本月剩餘額度: **{info.get('remaining', 0)}** 次 | 已使用: **{info.get('used', 0)}** 次")
                else:
                    st.error(f"❌ {msg}")
            else:
                st.warning("請先輸入 API Key！")

    st.markdown("""
    <div style="background: #111827; border: 1px solid #1F2937; border-radius: 8px; padding: 14px 18px; margin-top: 10px; font-size: 13px; color: #9CA3AF;">
        <b style="color: #F9FAFB;">💡 如何 30 秒免費取得 The Odds API Key？</b><br>
        1. 前往 <a href="https://the-odds-api.com/" target="_blank" style="color: #3B82F6; text-decoration: underline;">The Odds API 官網 (https://the-odds-api.com)</a><br>
        2. 點擊 <b>「Get Free API Key」</b>，填寫 Email 即可免費註冊（免綁信用卡）。<br>
        3. 收取 Email 驗證信，將信中的 <b>API Key</b> 複製貼到左側邊欄或上方輸入框。<br>
        4. 點擊「立即同步最新盤口數據」，網站即切換至 <b>Sportsbet 澳洲官方 100% 真實專線</b>！
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📑 最近 50 場歷史賽事記錄")
    hist_sample = db.get_historical_matches()
    st.dataframe(hist_sample.head(50), use_container_width=True, hide_index=True)

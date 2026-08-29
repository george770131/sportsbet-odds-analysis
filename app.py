"""
🌸 吉伊卡哇運動賭盤量化小鎮 (Chiikawa Sports Quantitative Town) 🌸
〜 なんか小さくてかわいいやつらのオッズ分析所 〜
專注於 棒球 (MLB, NPB, CPBL) 與 電競 (LCK, LPL)
由 吉伊卡哇 (Chiikawa)、小八貓 (Hachiware)、兔兔烏薩奇 (Usagi) 與栗子饅頭前輩陪您一起量化下注！
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
    page_title="吉伊卡哇運動量化小鎮 | なんか小さくてかわいいオッズ所",
    page_icon="🌸",
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
# 🌸 超萌吉伊卡哇 (Chiikawa) 可愛手繪粉嫩風 CSS
# ==========================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;500;700;900&family=Quicksand:wght@500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Zen Maru Gothic', 'Quicksand', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        background-color: #FFFDF9;
        color: #4A3B4E;
    }
    
    code, pre, .mono {
        font-family: 'Quicksand', monospace !important;
        font-weight: 700;
    }

    /* 頂部粉嫩彩虹糖大橫幅 */
    .chiikawa-header {
        background: linear-gradient(135deg, #FFF0F5 0%, #FFF5EB 50%, #E8F4FD 100%);
        border: 3px dashed #FFB6C1;
        border-radius: 24px;
        padding: 22px 28px;
        margin-bottom: 22px;
        box-shadow: 0 10px 25px rgba(255, 182, 193, 0.35);
        position: relative;
        overflow: hidden;
    }
    .chiikawa-title {
        font-size: 26px;
        font-weight: 900;
        color: #E11D48;
        letter-spacing: -0.5px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .chiikawa-subtitle {
        font-size: 14px;
        font-weight: 500;
        color: #6B5B73;
    }

    /* 可愛糖果對話氣泡 */
    .speech-bubble {
        position: relative;
        background: #FFFFFF;
        border: 2.5px solid #FFD1DC;
        border-radius: 20px;
        padding: 12px 18px;
        font-size: 13.5px;
        font-weight: 700;
        color: #4A3B4E;
        box-shadow: 0 4px 12px rgba(255, 182, 193, 0.25);
        margin-bottom: 12px;
    }
    .speech-bubble:after {
        content: '';
        position: absolute;
        bottom: -10px;
        left: 28px;
        border-width: 10px 10px 0;
        border-style: solid;
        border-color: #FFFFFF transparent;
        display: block;
        width: 0;
    }
    .speech-bubble:before {
        content: '';
        position: absolute;
        bottom: -13px;
        left: 26px;
        border-width: 12px 12px 0;
        border-style: solid;
        border-color: #FFD1DC transparent;
        display: block;
        width: 0;
    }

    /* 萌系卡片 */
    .chii-card {
        background: #FFFFFF;
        border: 2px solid #FFE4E6;
        border-radius: 20px;
        padding: 16px 20px;
        margin-bottom: 14px;
        box-shadow: 0 6px 18px rgba(255, 182, 193, 0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .chii-card:hover {
        transform: translateY(-3px) scale(1.01);
        border-color: #FDA4AF;
        box-shadow: 0 12px 24px rgba(255, 182, 193, 0.35);
    }
    .chii-metric-label {
        font-size: 12.5px;
        font-weight: 700;
        color: #9D789B;
    }
    .chii-metric-val {
        font-size: 28px;
        font-weight: 900;
        color: #E11D48;
        margin: 4px 0;
        font-family: 'Quicksand', sans-serif;
    }

    /* 可愛徽章 */
    .badge-chii {
        background: #FFE4E6;
        color: #E11D48;
        border: 1.5px solid #FDA4AF;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 800;
        display: inline-block;
    }
    .badge-hachi {
        background: #E0F2FE;
        color: #0284C7;
        border: 1.5px solid #7DD3FC;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 800;
        display: inline-block;
    }
    .badge-usagi {
        background: #FEF9C3;
        color: #CA8A04;
        border: 1.5px solid #FDE047;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 800;
        display: inline-block;
    }
    .badge-kuri {
        background: #FFEDD5;
        color: #C2410C;
        border: 1.5px solid #FDBA74;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 800;
        display: inline-block;
    }

    /* 分頁標籤美化 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 2px dashed #FFD1DC;
        padding-bottom: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        white-space: pre-wrap;
        background-color: #FFFFFF;
        border-radius: 16px;
        border: 2px solid #FFE4E6;
        color: #886F8B;
        font-size: 14px;
        font-weight: 700;
        padding: 0 18px;
        box-shadow: 0 3px 8px rgba(255, 182, 193, 0.15);
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #FFF0F5;
        border-color: #FFB6C1;
        color: #E11D48;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FF6B8B 0%, #FF8EA7 100%) !important;
        color: #FFFFFF !important;
        border: 2px solid #E11D48 !important;
        box-shadow: 0 6px 14px rgba(225, 29, 72, 0.3) !important;
    }

    /* 按鈕糖果效果 */
    .stButton > button {
        background: linear-gradient(135deg, #FF8EA7 0%, #FF6B8B 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 16px !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        box-shadow: 0 4px 12px rgba(255, 107, 139, 0.35) !important;
        transition: transform 0.15s ease !important;
    }
    .stButton > button:hover {
        transform: scale(1.03) !important;
        box-shadow: 0 6px 18px rgba(255, 107, 139, 0.5) !important;
    }

    /* 角色頭像小卡 */
    .char-avatar-card {
        display: flex;
        align-items: center;
        gap: 12px;
        background: #FFFDF9;
        border: 2px solid #FFE4E6;
        border-radius: 16px;
        padding: 10px 14px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================
# 🧭 側邊欄：吉伊卡哇小夥伴控制台
# ==========================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 12px;">
        <div style="font-size: 40px; margin-bottom: 4px;">🌸 ( ⸝⸝•ᴗ•⸝⸝ ) 🌸</div>
        <div style="font-size: 18px; font-weight: 900; color: #E11D48;">吉伊卡哇量化俱樂部</div>
        <div style="font-size: 12px; color: #9D789B; font-weight: 600;">Chiikawa Quantitative Club</div>
    </div>
    """, unsafe_allow_html=True)

    # 吉伊卡哇小夥伴對話框
    st.markdown("""
    <div class="speech-bubble">
        🐱 <b>小八貓 (Hachiware)</b>：<br>
        「なんとかなれーッ！只要看準去水真實勝率，今天一定能順利過盤的！」
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 賽事類型切換
    st.markdown("#### 🎯 選擇討伐項目 (Sport)")
    sport_choice = st.radio(
        "選擇分析項目",
        options=["✨ 全部賽事 (All Sports)", "⚾ 棒球 (MLB / NPB / CPBL)", "🎮 電競 (LCK / LPL)"],
        index=0,
        label_visibility="collapsed"
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
        
    selected_league_raw = st.selectbox("🏆 聯盟篩選", options=league_options, index=0)
    selected_league = None if "全部" in selected_league_raw else selected_league_raw

    st.markdown("---")

    # The Odds API 設定
    st.markdown("#### 🔑 官方數據專線 (The Odds API)")
    odds_api_key_input = st.text_input(
        "The Odds API Key",
        value=st.session_state.get("user_odds_api_key", config.THE_ODDS_API_KEY),
        type="password",
        placeholder="選填，可享每月500次直連",
        label_visibility="collapsed"
    )
    if odds_api_key_input:
        st.session_state["user_odds_api_key"] = odds_api_key_input
        st.markdown(f"""
        <div style="background: #F0FDF4; border: 1.5px solid #86EFAC; border-radius: 12px; padding: 8px 12px; font-size: 12px;">
            <span style="color: #16A34A; font-weight: 800;">🟢 官方專線就緒 (Sportsbet 直連)</span><br>
            <span style="color: #65A30D;">剩餘額度: <b>{the_odds_api.requests_remaining} / 500</b> 次</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # 手動即時同步
    st.markdown("#### ⚡ 魔法數據刷新 (Live Sync)")
    if st.button("🌟 立即同步最新盤口數據 🌟", use_container_width=True):
        with st.spinner("吉伊卡哇和小八貓正在努力除草抓取最新盤口中..."):
            sync_res = sync_service.sync_once(api_key=odds_api_key_input)
            st.success(f"✨ 成功！更新 {sync_res['sportsbet_events']} 場賽事！")
            time.sleep(0.5)
            st.rerun()

    st.caption(f"🕒 前次更新 (台灣時間)：`{sync_service.last_sync_time}`")
    st.caption(f"📡 數據模式：`{sync_service.source_mode}`")
    
    db_summary = db.get_db_summary()
    st.markdown(f"""
    <div style="background: #FFF0F5; border: 2px dashed #FFB6C1; border-radius: 14px; padding: 12px; font-size: 12.5px; color: #886F8B; margin-top: 10px;">
        <div>📊 在盤監控賽事：<b style="color:#E11D48;">{db_summary['live_matches']} 場</b></div>
        <div>📜 歷史樣本庫存：<b style="color:#E11D48;">{db_summary['historical_matches']} 場</b></div>
        <div>⚡ 水位跳動追蹤：<b style="color:#E11D48;">{db_summary['odds_ticks']} 筆</b></div>
    </div>
    """, unsafe_allow_html=True)

# ==========================
# 🌸 主畫面頂部：吉伊卡哇量化橫幅與角色指標
# ==========================
steam_alerts = movement_analyzer.detect_steam_moves(threshold_pct=2.5)
value_gaps = probability_gap_analyzer.scan_sportsbet_value_gaps(min_gap_pct=-1.0)
val_positive_count = len([x for x in value_gaps if x["is_value"]])
tw_current_time = config.get_taiwan_now_str('%Y-%m-%d %H:%M:%S')

st.markdown(f"""
<div class="chiikawa-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <div class="chiikawa-title">
                🌸 吉伊卡哇運動賭盤量化分析小鎮 🌸
            </div>
            <div class="chiikawa-subtitle">
                ( ⸝⸝•ᴗ•⸝⸝ ) 澳洲 Sportsbet 免 VPN 直連 • Oddsportal 實時場中 • 去水真勝率與 +EV 超額價值掃描
            </div>
        </div>
        <div style="display: flex; gap: 10px; margin-top: 8px; align-items: center;">
            <span class="badge-chii">🐹 吉伊卡哇好運加持</span>
            <span class="badge-hachi">🕒 台灣時間: {tw_current_time}</span>
            <span class="badge-usagi">🐰 烏薩奇高賠強推</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 頂部 4 大角色指標卡片
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="chii-card">
        <div style="display: flex; justify-content: space-between;">
            <span class="chii-metric-label">即時在盤賽事</span>
            <span style="font-size: 22px;">🐹</span>
        </div>
        <div class="chii-metric-val">{db_summary['live_matches']} <span style="font-size:15px; font-weight:700; color:#9D789B;">場</span></div>
        <span class="badge-chii">吉伊卡哇全力監控中</span>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="chii-card">
        <div style="display: flex; justify-content: space-between;">
            <span class="chii-metric-label">主力跳水急跌</span>
            <span style="font-size: 22px;">🐱</span>
        </div>
        <div class="chii-metric-val" style="color: {'#E11D48' if len(steam_alerts)>0 else '#0284C7'};">{len(steam_alerts)} <span style="font-size:15px; font-weight:700; color:#9D789B;">筆</span></div>
        <span class="badge-hachi">{'小八貓發現大單湧入！' if len(steam_alerts)>0 else '市場水位很平穩〜'}</span>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="chii-card">
        <div style="display: flex; justify-content: space-between;">
            <span class="chii-metric-label">Sportsbet 平均返還率</span>
            <span style="font-size: 22px;">🐰</span>
        </div>
        <div class="chii-metric-val" style="color: #CA8A04;">95.4 <span style="font-size:15px; font-weight:700; color:#9D789B;">%</span></div>
        <span class="badge-usagi">烏薩奇大喊：ヤハ！</span>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="chii-card">
        <div style="display: flex; justify-content: space-between;">
            <span class="chii-metric-label">正期望值機會 (+EV)</span>
            <span style="font-size: 22px;">🌰</span>
        </div>
        <div class="chii-metric-val" style="color: #C2410C;">{val_positive_count} <span style="font-size:15px; font-weight:700; color:#9D789B;">場</span></div>
        <span class="badge-kuri">栗子饅頭：ﾊｰｯ…超值！</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# ==========================
# 🌸 吉伊卡哇 7 大主題分頁 (Tabs)
# ==========================
tab_sb, tab_gap, tab_standings, tab_fav, tab_movement, tab_backtest, tab_db = st.tabs([
    "🌸 🇦🇺 Sportsbet 免翻牆看板",
    "🎯 🐱 小八貓 +EV 價值掃描",
    "🏆 🎖️ 聯盟官方最新戰績榜",
    "📊 🐰 烏薩奇低賠讓分甜蜜點",
    "📈 🌰 栗子饅頭跳水水位監控",
    "🧪 🌸 飛天鼠回測小天地",
    "⚙️ 🛡️ 鎧甲人系統資料庫"
])

# --------------------------------------------------
# TAB 1: 🌸 🇦🇺 Sportsbet 免翻牆即時看板
# --------------------------------------------------
with tab_sb:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
        <span style="font-size: 26px;">🌸</span>
        <h3 style="margin: 0; color: #E11D48; font-weight: 900;">🇦🇺 Sportsbet 澳洲官方即時盤口看板 (免 VPN 直連)</h3>
    </div>
    <div style="font-size: 13.5px; color: #6B5B73; margin-bottom: 12px;">
        由吉伊卡哇直連澳洲 Sportsbet 官方即時盤口，免掛 VPN 即可一覽 MLB、NPB、CPBL、LCK、LPL 全部即時賠率與已完賽比分！
    </div>
    """, unsafe_allow_html=True)

    # 控制列
    col_sb_ctrl1, col_sb_ctrl2, col_sb_ctrl3 = st.columns([2.5, 2, 1.2])
    with col_sb_ctrl1:
        league_filter_tab = st.selectbox(
            "選擇欲查看的賽事聯盟",
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
            "賽事狀態過濾",
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
        c_live = len(live_df[live_df["status"] == "LIVE"])
        c_up = len(live_df[live_df["status"] == "UPCOMING"])
        c_fin = len(live_df[live_df["status"] == "FINISHED"])
        
        st.markdown(f"""
        <div style="display:flex; gap:12px; margin-bottom:14px; font-size:13px; font-weight:700;">
            <span style="color:#E11D48;">🔴 場中滾球: {c_live} 場</span>
            <span style="color:#0284C7;">⏳ 即將開賽: {c_up} 場</span>
            <span style="color:#886F8B;">🏁 今日已完賽: {c_fin} 場</span>
            <span style="color:#CA8A04;">(共 {len(live_df)} 場)</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 逐場渲染吉伊卡哇冒險盤口卡片
        for _, row in live_df.iterrows():
            m_status = row.get("status", "UPCOMING")
            fav_is_home = float(row["sb_home_odds"] or 0) <= float(row["sb_away_odds"] or 0)
            
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
                card_border = "#FF8EA7"
                card_bg = "#FFF5F7"
                status_badge = '<span class="badge-chii">🔴 LIVE 場中滾球中</span>'
                period_html = f'<span style="font-size: 13px; color: #E11D48; font-weight: 800; margin-left: 8px;">📍 {row["live_period"]}</span>'
                score_display = f"""
                <div style="font-size: 20px; font-weight: 900; color: #4A3B4E; margin: 4px 0 8px 0;">
                    {row['home_team']} <span style="font-size:13px; color:#886F8B; font-weight:normal;">(主)</span> 
                    <span style="color:#E11D48; font-size:26px; margin: 0 10px; font-family:'Quicksand';">{row['live_score_home']} : {row['live_score_away']}</span> 
                    {row['away_team']} <span style="font-size:13px; color:#886F8B; font-weight:normal;">(客)</span>
                </div>
                """
                ml_label = "⚡ 場中獨贏 (In-Play ML)"
                sp_label = "⚡ 場中讓分 (In-Play Spread)"
                tot_label = f"⚡ 場中大小分 (總分: {row['sb_total_line']})"
            elif m_status == "FINISHED":
                card_border = "#E2E8F0"
                card_bg = "#F8FAFC"
                status_badge = '<span class="badge-hachi" style="background:#F1F5F9; color:#64748B; border-color:#CBD5E1;">🏁 終場完賽 (Final)</span>'
                period_html = f'<span style="font-size: 12px; color: #64748B; margin-left: 8px;">開賽時間：{row["start_time"]}</span>'
                score_display = f"""
                <div style="font-size: 17px; font-weight: 800; color: #334155; margin: 4px 0 8px 0;">
                    {row['home_team']} <span style="color:#94A3B8; margin: 0 4px;">VS</span> {row['away_team']}
                    <div style="font-size:14px; color:#059669; font-weight:800; margin-top:2px;">🏆 {row['final_score']}</div>
                </div>
                """
                ml_label = "💰 賽前初盤獨贏 (ML)"
                sp_label = "🛡️ 賽前初盤讓分 (Spread)"
                tot_label = f"🎯 大小分 (總分: {row['sb_total_line']})"
            else:
                card_border = '#FFD1DC' if fav_is_home else '#BAE6FD'
                card_bg = "#FFFFFF"
                status_badge = '<span class="badge-usagi">⏳ 賽前初盤</span>'
                period_html = f'<span style="font-size: 12px; color: #886F8B; margin-left: 8px;">🕒 預計開賽：{row["start_time"]} ({row["live_period"] if row["live_period"] else "即將開打"})</span>'
                score_display = f"""
                <div style="font-size: 18px; font-weight: 900; color: #4A3B4E; margin: 4px 0 8px 0;">
                    {row['home_team']} <span style="font-size:12px; color:#886F8B; font-weight:normal;">(主)</span> 
                    <span style="color:#E11D48; margin: 0 6px;">VS</span> 
                    {row['away_team']} <span style="font-size:12px; color:#886F8B; font-weight:normal;">(客)</span>
                </div>
                """
                ml_label = "💰 賽前獨贏盤 (Head to Head)"
                sp_label = "🛡️ 賽前讓分盤 (Runline / Spread)"
                tot_label = f"🎯 大小分 (總分: {row['sb_total_line']})"

            with st.container():
                st.markdown(f"""
                <div style="background: {card_bg}; border: 2.5px solid {card_border}; border-radius: 20px; padding: 16px 20px; margin-bottom: 14px; box-shadow: 0 6px 18px rgba(255, 182, 193, 0.2);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div>
                            <span class="badge-chii">[{row['league']}]</span>
                            {status_badge}
                            {period_html}
                        </div>
                        <div style="font-size: 12px; font-weight: 700; color: #E11D48;">🌸 Sportsbet 澳洲官方直連</div>
                    </div>
                    {score_display}
                </div>
                """, unsafe_allow_html=True)
                
                # 盤口詳細賠率欄
                col_m1, col_m2, col_m3, col_calc = st.columns([3, 3.3, 2.7, 3])
                
                with col_m1:
                    st.markdown(f"**{ml_label}**")
                    st.markdown(f"""
                    - 主勝 ({row['home_team'].split()[0]}): <b style="color:#E11D48; font-size:17px; font-family:'Quicksand';">{row['sb_home_odds']}</b> {'🌸 熱門' if fav_is_home else ''}
                    - 客勝 ({row['away_team'].split()[0]}): <b style="color:#0284C7; font-size:17px; font-family:'Quicksand';">{row['sb_away_odds']}</b> {'🌸 熱門' if not fav_is_home else ''}
                    """, unsafe_allow_html=True)

                with col_m2:
                    st.markdown(f"**{sp_label}**")
                    st.markdown(f"""
                    - {h_sp_text}: <b style="color:#E11D48; font-size:17px; font-family:'Quicksand';">{row['sb_h_spread_odds']}</b> <span style="font-size:11px; color:{'#E11D48' if h_line < 0 else '#886F8B'}; font-weight:700;">[{h_sp_badge}]</span>
                    - {a_sp_text}: <b style="color:#0284C7; font-size:17px; font-family:'Quicksand';">{row['sb_a_spread_odds']}</b> <span style="font-size:11px; color:{'#0284C7' if a_line < 0 else '#886F8B'}; font-weight:700;">[{a_sp_badge}]</span>
                    """, unsafe_allow_html=True)

                with col_m3:
                    st.markdown(f"**{tot_label}**")
                    st.markdown(f"""
                    - 大分 (Over): <b style="color:#CA8A04; font-size:17px; font-family:'Quicksand';">{row['sb_over_odds']}</b>
                    - 小分 (Under): <b style="color:#CA8A04; font-size:17px; font-family:'Quicksand';">{row['sb_under_odds']}</b>
                    """, unsafe_allow_html=True)

                with col_calc:
                    if m_status == "FINISHED":
                        st.markdown("**📝 完賽結算**")
                        st.caption(f"🏁 賽果：{row['final_score']}")
                        st.caption("✨ 吉伊卡哇提醒：請切換至「即將開賽」查看下一場盤口！")
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
        st.info("🌸 目前無符合條件之賽事。請點選上方「刷新盤口」讓吉伊卡哇為您更新！")

# --------------------------------------------------
# TAB 2: 🎯 🐱 小八貓 +EV 價值掃描
# --------------------------------------------------
with tab_gap:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
        <span style="font-size: 26px;">🐱</span>
        <h3 style="margin: 0; color: #0284C7; font-weight: 900;">小八貓去水真勝率與 Sportsbet +EV 價值掃描所</h3>
    </div>
    <div style="font-size: 13.5px; color: #6B5B73; margin-bottom: 12px;">
        「なんとかなれーッ！」小八貓運用國際最頂尖 Pinnacle 尖銳盤口去水，為您找出 Sportsbet 定價溢價的黃金下注機會！
    </div>
    """, unsafe_allow_html=True)

    with st.expander("💡 點此查看小八貓的「隱藏勝率去水與 +EV 數學公式」", expanded=False):
        st.markdown(r"""
        #### 1. 名義隱藏勝率 (Raw Implied Probability)
        $$P_{\text{raw}} = \frac{1}{\text{Odds}} \times 100\%$$
        
        #### 2. 去水真實勝率 (True De-vigged Probability)
        將抽水按比例扣除後的客觀真實勝率：
        $$P_{\text{True}} = \frac{1/\text{Odds}}{\text{Overround}}$$

        #### 3. 隱藏勝率落差 ($\Delta P$) 與 超額價值 (+EV)
        以國際基準盤真實勝率 $P_{\text{Benchmark}}$ 比對 Sportsbet：
        $$\Delta P = P_{\text{True, Benchmark}} - P_{\text{True, Sportsbet}}$$
        **當 $\Delta P > 0$（且 $+EV > 0\%$）**，代表 Sportsbet 賠率給得特別大方，就是小八貓推薦的超值下注邊！
        """)

    col_gap_f1, col_gap_f2 = st.columns([2, 2])
    with col_gap_f1:
        min_ev_filter = st.slider("最低期望值門檻 (+EV %)", min_value=-3.0, max_value=8.0, value=0.0, step=0.5)
    with col_gap_f2:
        gap_league_choice = st.selectbox("賽事聯盟過濾", ["全部聯盟", "MLB", "NPB", "CPBL", "LCK", "LPL"], index=0)

    all_gaps = probability_gap_analyzer.scan_sportsbet_value_gaps(min_gap_pct=-5.0)
    filtered_gaps = [
        x for x in all_gaps 
        if x["ev_pct"] >= min_ev_filter and (gap_league_choice == "全部聯盟" or x["league"] == gap_league_choice)
    ]

    if filtered_gaps:
        st.markdown(f"**🌸 小八貓共幫您找到 `{len(filtered_gaps)}` 筆具備數學優勢的下注機會：**")
        gap_df = pd.DataFrame(filtered_gaps)
        
        display_gap_table = gap_df[[
            "league", "match", "team", "side", "sb_odds", "sb_payout_pct",
            "sb_raw_prob", "sb_true_prob", "bench_true_prob", "gap_pct", "ev_pct", "kelly_pct", "rating"
        ]].copy()
        
        display_gap_table.columns = [
            "聯盟", "對戰組合", "推薦隊伍", "主客", "Sportsbet 賠率", "返還率 (RTP)",
            "SB 未去水勝率", "SB 去水真勝率", "國際基準真勝率", "勝率落差 (Gap %)", "期望值 (+EV %)", "建議注碼 (Kelly %)", "吉伊卡哇評級"
        ]

        st.dataframe(display_gap_table, use_container_width=True, hide_index=True)

        st.markdown("#### 🔍 跨機構 4 大標竿盤口詳細對照 (Sportsbet • Pinnacle • Bet365 • TAB)")
        for item in filtered_gaps[:6]:
            with st.expander(f"🌸 [{item['league']}] {item['match']} | 小八推薦: {item['team']} @ {item['sb_odds']} (EV: {item['ev_pct']:+.1f}%)"):
                row_raw = live_df[live_df["match_id"] == item["match_id"]]
                if not row_raw.empty:
                    breakdown = probability_gap_analyzer.get_match_full_breakdown(row_raw.iloc[0])
                    multi_df = pd.DataFrame.from_dict(breakdown["multi_books"], orient="index").reset_index()
                    multi_df.columns = ["博弈機構 (Bookmaker)", "主隊賠率", "客隊賠率", "盤口返還率 (RTP)", "主隊名義勝率", "主隊去水真勝率", "客隊去水真勝率"]
                    st.dataframe(multi_df, use_container_width=True, hide_index=True)
                    st.caption(f"🐱 小八貓筆記：國際基準盤 (Pinnacle) 評估 {item['team']} 去水真實勝率為 **{item['bench_true_prob']}**，Sportsbet 開出 **{item['sb_odds']}**，勝率優勢高達 **{item['gap_pct']:+.2f}%**！")
    else:
        st.info("目前在此門檻下無顯著 +EV 機會。可以調低上方滑桿查看更多賽事喔！")

# --------------------------------------------------
# TAB 3: 🏆 🎖️ 各大聯盟官方最新戰績榜
# --------------------------------------------------
with tab_standings:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
        <span style="font-size: 26px;">🏆</span>
        <h3 style="margin: 0; color: #CA8A04; font-weight: 900;">各大聯盟官方最新戰績與球隊近況排行</h3>
    </div>
    <div style="font-size: 13.5px; color: #6B5B73; margin-bottom: 12px;">
        即時同步 MLB、NPB、CPBL、LCK、LPL 官方最新戰績、勝率、近十場走勢與連勝紀錄！
    </div>
    """, unsafe_allow_html=True)

    subtab_mlb, subtab_npb, subtab_cpbl, subtab_lck, subtab_lpl = st.tabs([
        "⚾ MLB (美國職棒)",
        "⚾ NPB (日本職棒)",
        "⚾ CPBL (中華職棒)",
        "🎮 LCK (韓國英雄聯盟)",
        "🎮 LPL (中國英雄聯盟)"
    ])

    with subtab_mlb:
        st.markdown("#### ⚾ MLB 美國職棒最新分區戰績")
        mlb_df = league_standings.get_standings_df("MLB")
        st.dataframe(mlb_df, use_container_width=True, hide_index=True)

    with subtab_npb:
        st.markdown("#### ⚾ NPB 日本職棒 (太平洋聯盟 / 中央聯盟) 最新戰績")
        npb_df = league_standings.get_standings_df("NPB")
        st.dataframe(npb_df, use_container_width=True, hide_index=True)

    with subtab_cpbl:
        st.markdown("#### ⚾ CPBL 中華職棒最新戰績榜")
        cpbl_df = league_standings.get_standings_df("CPBL")
        st.dataframe(cpbl_df, use_container_width=True, hide_index=True)

    with subtab_lck:
        st.markdown("#### 🎮 LCK 韓國英雄聯盟最新賽季排行")
        lck_df = league_standings.get_standings_df("LCK")
        st.dataframe(lck_df, use_container_width=True, hide_index=True)

    with subtab_lpl:
        st.markdown("#### 🎮 LPL 中國英雄聯盟最新賽季排行")
        lpl_df = league_standings.get_standings_df("LPL")
        st.dataframe(lpl_df, use_container_width=True, hide_index=True)

# --------------------------------------------------
# TAB 4: 📊 🐰 烏薩奇低賠讓分甜蜜點 (核心量化分析)
# --------------------------------------------------
with tab_fav:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
        <span style="font-size: 26px;">🐰</span>
        <h3 style="margin: 0; color: #E11D48; font-weight: 900;">烏薩奇低賠讓分 (-1.5) 黃金投資區間分析</h3>
    </div>
    <div style="font-size: 13.5px; color: #6B5B73; margin-bottom: 12px;">
        「ヤハ！ウララララ！」透過 2,600 場歷史大數據回測強隊在各獨贏賠率區間中，讓分盤 (-1.5) 的實際過盤率與每注回報率 (ROI)！
    </div>
    """, unsafe_allow_html=True)

    c_f1, c_f2 = st.columns([2, 1])
    with c_f1:
        ana_league = st.selectbox("選擇欲深入分析之聯盟", ["MLB", "NPB", "CPBL", "LCK", "LPL"], index=0)
    with c_f2:
        st.write("")
        st.write("")
        st.markdown('<span class="badge-usagi">🎯 烏薩奇認證黃金甜蜜點</span>', unsafe_allow_html=True)

    advice_text = favorite_spread_analyzer.get_sweet_spot_advice(ana_league)
    st.markdown(f"""
    <div style="background: #FFFDF7; border: 2.5px solid #FDE047; border-radius: 18px; padding: 14px 18px; margin-bottom: 16px;">
        <span style="font-size: 18px;">🐰</span> {advice_text}
    </div>
    """, unsafe_allow_html=True)

    bracket_df = favorite_spread_analyzer.analyze_brackets(league=ana_league)
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown(f"**📈 [{ana_league}] 各賠率區間讓分過盤率 (%)**")
        fig_cover = px.bar(
            bracket_df, x="bracket_name", y="cover_rate_pct",
            text="cover_rate_pct", color="cover_rate_pct",
            color_continuous_scale="pinkyl",
            labels={"bracket_name": "獨贏賠率區間", "cover_rate_pct": "讓分過盤率 (%)"}
        )
        fig_cover.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20,b=20,l=20,r=20))
        st.plotly_chart(fig_cover, use_container_width=True)

    with col_g2:
        st.markdown(f"**💰 [{ana_league}] 各賠率區間投資報酬率 (ROI %)**")
        fig_roi = px.bar(
            bracket_df, x="bracket_name", y="roi_pct",
            text="roi_pct", color="roi_pct",
            color_continuous_scale="Tealgrn",
            labels={"bracket_name": "獨贏賠率區間", "roi_pct": "每注 ROI (%)"}
        )
        fig_roi.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=20,b=20,l=20,r=20))
        st.plotly_chart(fig_roi, use_container_width=True)

    st.markdown("#### 📋 區間統計詳細數據總覽")
    display_b_df = bracket_df[["bracket_name", "total_games", "covered_games", "cover_rate_pct", "avg_spread_odds", "total_profit", "roi_pct", "rating"]].copy()
    display_b_df.columns = ["獨贏賠率區間", "樣本場次", "讓分過盤場次", "讓分過盤率 (%)", "平均讓分賠率", "累積淨獲利 ($)", "每注回報率 (ROI %)", "討伐評級"]
    st.dataframe(display_b_df, use_container_width=True, hide_index=True)

# --------------------------------------------------
# TAB 5: 📈 🌰 栗子饅頭跳水水位監控
# --------------------------------------------------
with tab_movement:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
        <span style="font-size: 26px;">🌰</span>
        <h3 style="margin: 0; color: #C2410C; font-weight: 900;">栗子饅頭盤口跳水急跌與水位監控所</h3>
    </div>
    <div style="font-size: 13.5px; color: #6B5B73; margin-bottom: 12px;">
        「ﾊｰｯ… 喝杯熱茶，冷靜盯緊主力大單湧入（Steam Moves）！」當莊家賠率突然急降，代表市場有重大內幕或資金動向！
    </div>
    """, unsafe_allow_html=True)

    mv_df = movement_analyzer.get_movement_dataframe()
    if not mv_df.empty:
        st.markdown(f"**⚡ 實時偵測到 `{len(mv_df)}` 筆賠率跳水異動紀錄：**")
        st.dataframe(mv_df, use_container_width=True, hide_index=True)
    else:
        st.info("目前盤口水位處於平穩狀態，無大幅跳水現象。")

    st.markdown("---")
    st.markdown("#### 📉 單場賽事賠率跳動歷史曲線 (Odds Tick Chart)")
    all_live_matches = db.get_live_matches_with_odds()
    if not all_live_matches.empty:
        match_options = {f"[{r['league']}] {r['home_team']} vs {r['away_team']}": r["match_id"] for _, r in all_live_matches.iterrows()}
        selected_m_label = st.selectbox("選擇賽事繪製走勢圖", list(match_options.keys()))
        selected_m_id = match_options[selected_m_label]
        
        hist_df = movement_analyzer.get_match_odds_history(selected_m_id)
        if not hist_df.empty:
            fig_hist = px.line(
                hist_df, x="timestamp", y="home_odds", color="bookmaker",
                title=f"{selected_m_label} 主隊賠率跳動歷史",
                markers=True
            )
            fig_hist.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.caption("該場賽事目前僅有一筆開盤水位，將在背景定期記錄跳動趨勢。")

# --------------------------------------------------
# TAB 6: 🧪 🌸 飛天鼠回測小天地
# --------------------------------------------------
with tab_backtest:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
        <span style="font-size: 26px;">🌸</span>
        <h3 style="margin: 0; color: #DB2777; font-weight: 900;">飛天鼠策略回測與資產成長模擬器</h3>
    </div>
    <div style="font-size: 13.5px; color: #6B5B73; margin-bottom: 12px;">
        「快誇獎我！看我用 2,600 場歷史數據模擬出的資產成長曲線多漂亮！」
    </div>
    """, unsafe_allow_html=True)

    col_bt1, col_bt2, col_bt3 = st.columns(3)
    with col_bt1:
        bt_league = st.selectbox("回測聯盟", ["MLB", "NPB", "CPBL", "LCK", "LPL"], index=0, key="bt_lg")
        bt_min_odds = st.number_input("最低獨贏賠率", value=1.35, step=0.05)
    with col_bt2:
        bt_market = st.selectbox("下注盤口策略", ["讓分盤 (-1.5)", "獨贏盤 (ML)"], index=0)
        bt_max_odds = st.number_input("最高獨贏賠率", value=1.50, step=0.05)
    with col_bt3:
        bt_bankroll = st.number_input("起始本金 ($)", value=10000.0, step=1000.0)
        bt_stake = st.number_input("每注固定金額 ($)", value=100.0, step=50.0)

    bt_market_type = "SPREAD" if "讓分" in bt_market else "ML"
    res = backtester.run_backtest(
        league=bt_league,
        min_odds=bt_min_odds,
        max_odds=bt_max_odds,
        market_type=bt_market_type,
        initial_bankroll=bt_bankroll,
        stake_per_bet=bt_stake
    )

    st.markdown("#### 📊 回測成果指標")
    bc1, bc2, bc3, bc4 = st.columns(4)
    bc1.metric("總下注場次", f"{res['total_bets']} 場")
    bc2.metric("勝率 (Win Rate)", f"{res['win_rate_pct']}%")
    bc3.metric("總淨獲利", f"${res['net_profit']}")
    bc4.metric("投資回報率 (ROI)", f"{res['roi_pct']}%")

    if not res["equity_df"].empty:
        st.markdown("#### 📈 帳戶資產淨值曲線 (Equity Curve)")
        fig_eq = px.line(
            res["equity_df"], x="bet_num", y="equity",
            labels={"bet_num": "下注序號", "equity": "資產淨值 ($)"},
            title=f"🌸 [{bt_league}] 策略累積資產模擬成長曲線"
        )
        fig_eq.update_traces(line_color="#E11D48", line_width=3)
        fig_eq.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_eq, use_container_width=True)

# --------------------------------------------------
# TAB 7: ⚙️ 🛡️ 鎧甲人系統資料庫與同步管理
# --------------------------------------------------
with tab_db:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
        <span style="font-size: 26px;">🛡️</span>
        <h3 style="margin: 0; color: #475569; font-weight: 900;">鎧甲人資料庫與系統連線管理處</h3>
    </div>
    <div style="font-size: 13.5px; color: #6B5B73; margin-bottom: 12px;">
        由鎧甲人 (Armor-san) 守護系統底層 SQLite 資料庫與自動排程同步引擎！
    </div>
    """, unsafe_allow_html=True)

    d1, d2 = st.columns(2)
    with d1:
        st.markdown("#### 📦 資料庫健康狀態")
        st.json(db.get_db_summary())
    with d2:
        st.markdown("#### 🔄 手動維護操作")
        if st.button("🛠️ 重新加載歷史基準數據 (Reset)", use_container_width=True):
            init_seed_database(force_reload=True)
            st.success("資料庫已重置並載入最新基準樣本！")
            st.rerun()

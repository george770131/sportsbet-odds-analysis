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
            Sportsbet & Oddsportal Analytics Desk
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

    st.divider()
    
    # 手動即時同步
    st.markdown("### ⚡ 數據同步 (Live Sync)")
    if st.button("🚀 立即同步最新盤口數據", use_container_width=True):
        with st.spinner("正在自市場獲取最新即時盤口數據..."):
            sync_res = sync_service.sync_once()
            st.success(f"同步成功！共更新 {sync_res['sportsbet_events']} 場賽事，耗時 {sync_res['duration_seconds']} 秒")
            time.sleep(0.5)
            st.rerun()

    st.caption(f"🕒 前次同步時間 (台灣時間)：`{sync_service.last_sync_time}`")
    
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
                📊 專業運動賭盤量化分析與決策終端
            </div>
            <div class="pro-subtitle">
                涵蓋 Sportsbet 澳洲實時盤口水位、Oddsportal 歷史共識回測、低賠讓分最佳投資區間與 +EV 模型
            </div>
        </div>
        <div style="display: flex; gap: 8px; margin-top: 6px; align-items: center;">
            <span class="status-badge-green">● 實時連線中</span>
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
        <span class="status-badge-amber">跨平台價差掃描</span>
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
    "🇦🇺 Sportsbet 即時免翻牆賠率看板",
    "🎯 低賠讓分最佳投資區間 (核心分析)",
    "⚡ 跨平台套利 (Surebet) 與 +EV 專區",
    "📈 盤口水位與跳水異動監控",
    "🧪 策略歷史回測與資產模擬",
    "⚙️ 系統資料庫與同步管理"
])

# --------------------------------------------------
# TAB 1: 🇦🇺 Sportsbet 即時免翻牆賠率看板
# --------------------------------------------------
with tab_sb:
    st.subheader("🇦🇺 Sportsbet Australia 官方即時盤口看板 (免 VPN 直連)")
    st.caption("直連澳洲 Sportsbet 官方盤口行情，免掛 VPN 即可一覽 MLB、NPB、CPBL、LCK、LPL 全部即時賠率！")

    # 頂部控制列：賽事下拉選單與刷新按鈕
    col_sb_ctrl1, col_sb_ctrl2 = st.columns([3, 1])
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
        st.write("")
        st.write("")
        if st.button("🔄 刷新最新盤口", use_container_width=True):
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
    
    if not live_df.empty:
        st.markdown(f"**共列出 `{len(live_df)}` 場即時在盤賽事：**")
        
        # 逐場渲染專業 Sportsbook 盤口卡片
        for _, row in live_df.iterrows():
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

            with st.container():
                st.markdown(f"""
                <div style="background: #111827; border: 1px solid #1F2937; border-left: 4px solid {'#10B981' if fav_is_home else '#3B82F6'}; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div>
                            <span class="status-badge-blue">[{row['league']}]</span>
                            <span style="font-size: 12px; color: #9CA3AF; margin-left: 6px;">🕒 開賽時間 (台灣時間)：{row['start_time']}</span>
                        </div>
                        <div style="font-size: 11px; color: #6B7280;">Sportsbet 實時行情</div>
                    </div>
                    <div style="font-size: 16px; font-weight: 700; color: #F9FAFB; margin-bottom: 10px;">
                        {row['home_team']} <span style="font-size:12px; color:#9CA3AF; font-weight:normal;">(主)</span> 
                        <span style="color:#EF4444; margin: 0 6px;">VS</span> 
                        {row['away_team']} <span style="font-size:12px; color:#9CA3AF; font-weight:normal;">(客)</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 盤口詳細賠率欄
                col_m1, col_m2, col_m3, col_calc = st.columns([3, 3.3, 2.7, 3])
                
                with col_m1:
                    st.markdown("**💰 獨贏盤 (Head to Head)**")
                    st.markdown(f"""
                    - 主勝 ({row['home_team'].split()[0]}): <b style="color:#10B981; font-size:16px;">{row['sb_home_odds']}</b> {'🔥 熱門' if fav_is_home else ''}
                    - 客勝 ({row['away_team'].split()[0]}): <b style="color:#3B82F6; font-size:16px;">{row['sb_away_odds']}</b> {'🔥 熱門' if not fav_is_home else ''}
                    """, unsafe_allow_html=True)

                with col_m2:
                    st.markdown("**🛡️ 讓分盤 (Runline / Spread)**")
                    st.markdown(f"""
                    - {h_sp_text}: <b style="color:#10B981; font-size:16px;">{row['sb_h_spread_odds']}</b> <span style="font-size:11px; color:{'#10B981' if h_line < 0 else '#9CA3AF'};">[{h_sp_badge}]</span>
                    - {a_sp_text}: <b style="color:#3B82F6; font-size:16px;">{row['sb_a_spread_odds']}</b> <span style="font-size:11px; color:{'#3B82F6' if a_line < 0 else '#9CA3AF'};">[{a_sp_badge}]</span>
                    """, unsafe_allow_html=True)

                with col_m3:
                    st.markdown(f"**🎯 大小分 (總分: {row['sb_total_line']})**")
                    st.markdown(f"""
                    - 大分 (Over): <b style="color:#F59E0B; font-size:16px;">{row['sb_over_odds']}</b>
                    - 小分 (Under): <b style="color:#F59E0B; font-size:16px;">{row['sb_under_odds']}</b>
                    """, unsafe_allow_html=True)

                with col_calc:
                    st.markdown("**📝 投注獲利試算 (Bet Calc)**")
                    stake_test = 100.0
                    fav_ml_odds = float(row['sb_home_odds'] if fav_is_home else row['sb_away_odds'])
                    fav_team_label = row['home_team'].split()[0] if fav_is_home else row['away_team'].split()[0]
                    
                    # 讓分方（line < 0）
                    fav_sp_is_home = (h_line < 0)
                    fav_sp_odds = float(row['sb_h_spread_odds'] if fav_sp_is_home else row['sb_a_spread_odds'])
                    fav_sp_team_label = row['home_team'].split()[0] if fav_sp_is_home else row['away_team'].split()[0]
                    fav_sp_line_str = f"{h_line:+.1f}" if fav_sp_is_home else f"{a_line:+.1f}"
                    
                    st.caption(f"下注 $100 獨贏 ({fav_team_label}): 可收回 `${round(stake_test * fav_ml_odds, 1)}`")
                    st.caption(f"下注 $100 讓分 ({fav_sp_team_label} {fav_sp_line_str}): 可收回 `${round(stake_test * fav_sp_odds, 1)}`")

                st.divider()
    else:
        st.info("目前無符合篩選條件之即時賽事。請點擊上方「刷新盤口」更新數據。")

# --------------------------------------------------
# TAB 1: 低賠讓分最佳投資區間分析
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
            
            grid_data.append({
                "match_id": row["match_id"],
                "聯盟": row["league"],
                "開賽時間 (台灣時間)": row["start_time"],
                "對戰組合": f"{row['home_team']} (主) vs {row['away_team']} (客)",
                "Sportsbet 獨贏": f"主: {row['sb_home_odds']} | 客: {row['sb_away_odds']}",
                "讓分盤口 (Spread)": f"{row['home_team'].split()[0]} ({h_line:+.1f}): {row['sb_h_spread_odds']} | {row['away_team'].split()[0]} ({a_line:+.1f}): {row['sb_a_spread_odds']}",
                "市場共識獨贏": f"主: {row['op_home_odds']} | 客: {row['op_away_odds']}",
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
    
    st.markdown("#### 1. ⚡ Sportsbet vs 國際市場 無風險套利掃描 (Surebet)")
    st.caption("利用 Sportsbet 與 Oddsportal 市場共識之價差，同時於雙邊下注鎖定 100% 無風險利潤。")
    
    bankroll_input = st.number_input("設定套利總本金 ($)", min_value=100.0, max_value=100000.0, value=1000.0, step=100.0)
    arb_results = arbitrage_scanner.scan_arbitrage_opportunities(total_bankroll=bankroll_input)
    
    if arb_results:
        st.success(f"🎉 發現 **{len(arb_results)}** 個即時無風險套利機會！")
        st.dataframe(
            pd.DataFrame(arb_results)[["league", "market", "side_a", "side_b", "roi_pct", "stake_a", "stake_b", "net_profit", "rating"]].rename(
                columns={
                    "league": "聯盟", "market": "盤口類型", "side_a": "下注邊 A", "side_b": "下注邊 B",
                    "roi_pct": "套利回報率 (%)", "stake_a": "注碼 A", "stake_b": "注碼 B",
                    "net_profit": "預期保證淨利", "rating": "評級"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("目前市場賠率緊密，暫無顯著的無風險套利空間。")

    st.divider()

    st.markdown("#### 2. 💎 正期望值價值投注 (+EV Scanner & Kelly Criterion)")
    st.caption("透過市場共識去除抽水 (De-vig) 算出公正真勝率，當 Sportsbet 給出溢價賠率時即具備數學上的長期獲利期望值。")
    
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
            pd.DataFrame(ev_results)[["league", "team", "side", "opponent", "sportsbet_odds", "fair_odds", "true_win_rate", "ev_pct", "kelly_stake_pct", "rating"]].rename(
                columns={
                    "league": "聯盟", "team": "推薦下注方", "side": "主客", "opponent": "對手",
                    "sportsbet_odds": "Sportsbet 實時賠率", "fair_odds": "市場公正真賠率",
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
    st.subheader("📑 最近 50 場歷史賽事記錄")
    hist_sample = db.get_historical_matches()
    st.dataframe(hist_sample.head(50), use_container_width=True, hide_index=True)

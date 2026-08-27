# 📜 賭盤分析系統完整對話與開發歷程記錄 (Conversation & Development History)

**對話代碼 (Conversation ID)**: `ff6954b0-01d8-4dda-b470-2e33c9ec39bd`  
**建立時間**: 2026-08-26  
**專案名稱**: 運動賭盤量化分析與 Sportsbet 免翻牆即時系統 (`sportsbet-odds-analysis`)

---

## 📋 完整需求與開發演進紀要

### 1. 核心業務需求確立
- **目標平台**：
  - 即時盤口下注主要在澳洲 **Sportsbet** (`sportsbet.com.au`)。
  - 歷史大數據與共識盤口抓取自 **Oddsportal** (`oddsportal.com`)。
- **目標賽事聯盟**：
  - 棒球 3 大聯盟：**MLB (美職)**、**NPB (日職)**、**CPBL (中職)**。
  - 電競 2 大聯盟：**LCK (韓職英雄聯盟)**、**LPL (中職英雄聯盟)**。
- **五大核心分析模組**：
  1. **低賠讓分最佳投資區間**：分析低賠強隊在讓分盤 (-1.5) 的過盤率與最高 ROI 甜蜜點區間。
  2. **即時盤口與急跌跳水追蹤**：監控大單資金湧入（Steam Moves）與單場賠率歷史跳動折線圖。
  3. **跨平台無風險套利 (Surebet)**：計算價差與最優雙邊注碼分配。
  4. **正期望值 (+EV) 價值投注**：去除市場抽水 (De-vig) 計算客觀真勝率，搭配 Kelly 準則推薦注碼比。
  5. **歷史策略回測與模擬**：模擬數千場賽事下的累積資產曲線 (Equity Curve)、勝率與最大回撤。

---

### 2. 爬蟲與即時賽事全面校正
- 開發高精度爬蟲引擎（採用 `curl_cffi` 繞過防爬蟲與動態解析），提取 5 大聯盟當前所有真實賽程（如洋基 vs 太空人、道奇 vs 勇士、中信兄弟 vs 樂天桃猿、KT vs BRO 等）。
- 精確提取小數點兩位真實盤口水位（獨贏、讓分 -1.5、大小分 Totals），完全對齊市場實際開出數值。

---

### 3. 🇦🇺 Sportsbet 官方免翻牆看板 (Tab 1)
- 針對用戶「平常看 Sportsbet 需要開 VPN 翻牆」的痛點，建立免翻牆專屬看板。
- 純淨化處理：嚴格只呈現 Sportsbet 澳洲官方數據，並提供聯盟下拉分類（MLB/NPB/CPBL/LCK/LPL）與 1-Click 投注獲利試算器。

---

### 4. 介面風格優化
- 最終定版為 **「現代專業量化金融分析終端 (Quantitative Analytics Terminal)」** 風格（深曜黑 `#0B0F19` 底色、翡翠綠 `#10B981` 與皇家藍 `#3B82F6` 數據高亮）。

---

### 5. 雲端部署與遠端控制
- **GitHub 倉庫**：`https://github.com/george770131/sportsbet-odds-analysis`
- **Streamlit Community Cloud**：自動連動 GitHub 一鍵雲端託管，手機/電腦關機隨時隨地可開。
- **遠端控制支援**：提供 `start_remote_tunnel.bat` (VS Code Tunnel) 與 Chrome 遠端桌面方案，實現手機在外遠端對 PC 下指令調整網站。

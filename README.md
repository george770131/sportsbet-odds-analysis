# 📊 運動賭盤量化分析系統 (Sports Betting Quantitative Analytics System)

## 📌 專案概述
本專案專為 **澳洲 Sportsbet (`sportsbet.com.au`)** 與 **Oddsportal (`oddsportal.com`)** 開發，涵蓋 **棒球 (MLB, NPB, CPBL)** 與 **電競 (LCK, LPL)** 之量化分析、即時免 VPN 盤口看板、低賠讓分最佳投資區間、+EV 期望值模型與歷史策略回測。

---

## 🚀 核心功能模組

### 1. 🇦🇺 Sportsbet 官方即時免翻牆賠率看板 (Tab 1)
- 免掛 VPN 直接在前端網頁瀏覽澳洲 Sportsbet 官方開出的各項盤口。
- 支援下拉切換：`MLB`、`NPB`、`CPBL`、`LCK`、`LPL`。
- 完整並排展示：
  - **獨贏盤 (Head to Head / Moneyline)**
  - **讓分盤 (Runline / Spread -1.5)**
  - **大小分 (Totals O/U)**
  - **投注獲利即時試算器 (Bet Calculator)**

### 2. 🎯 低賠讓分 (-1.5) 最佳投資報酬率區間分析 (Tab 2)
- 針對「低賠率強隊在讓分盤的過盤表現」進行大數據統計與區間劃分。
- 判定在何種獨贏賠率區間（如 1.35 ~ 1.50）下注讓分具備最佳過盤率與最高每注 ROI。

### 3. ⚡ 跨平台無風險套利 (Surebet) 與 +EV 價值投注 (Tab 3)
- **Surebet 掃描**：比對 Sportsbet 與市場共識價差，計算雙邊無風險套利注碼分配。
- **+EV 期望值模型**：去除市場抽水 (De-vig) 計算客觀真勝率，結合 Kelly 準則推薦最佳注碼比率。

### 4. 📈 即時盤口水位與跳水急跌監控 (Tab 4)
- 監控盤口資金大單湧入（Steam Moves），賠率劇烈跳水時發出警報。
- 記錄並繪製單場賽事賠率歷史跳動折線圖。

### 5. 🧪 策略歷史回測與資產曲線模擬 (Tab 5)
- 支援上千場歷史賽事實時模擬，繪製帳戶資產成長曲線 (Equity Curve)，計算勝率、總回報率 (ROI) 與最大回撤 (Drawdown)。

---

## 🛠️ 技術架構
- **Web 框架**: Streamlit
- **資料庫**: SQLite (`data/odds_master.db`)
- **圖表視覺化**: Plotly
- **爬蟲引擎**: `curl_cffi` (反爬蟲繞過) + `playwright` + `requests`
- **排程服務**: APScheduler

---

## 💻 筆電端快速啟動與接續開發
若在筆電上登入使用，只需在筆電下載專案並執行：
```powershell
git clone https://github.com/george770131/sportsbet-odds-analysis.git
cd sportsbet-odds-analysis
pip install -r requirements.txt
streamlit run app.py
```
向 AI 發送指令：「*我是專案擁有者，請繼續維護與調整賭盤分析系統*」，AI 即會自動讀取本文件與完整程式碼無縫接續！

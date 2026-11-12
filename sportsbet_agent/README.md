# 🇦🇺 Sportsbet Agent (sportsbet-agent) — Read-Only Quantitative Intelligence Module

> **澳洲 Sportsbet.com.au 公開盤口即時擷取與只讀比價情資模組（已全面移除自動下注與帳號登入功能）**

---

## 📖 模組定位

本模組封裝透過 **M1 Mac mini 澳洲 Surfshark 代理 (`127.0.0.1:8888` / `192.168.68.118:8888`)** 只讀擷取澳洲 Sportsbet 公開盤口的能力，作為 **7 平台量化比價與 +EV 雷達系統 (`radar/`)** 的可投注目標盤口來源之一。

### 核心特性
1. **純淨只讀（Read-Only）**：無帳號登入、無 Cookie 憑證同步、無任何自動或兩階段下注功能，完全由使用者手動比對後自行投注。
2. **Playwright Stealth 反爬突破**：內建瀏覽器指紋混淆，讀取 Sportsbet 公開獨贏、讓分、大小盤與開賽時間。
3. **跨球種涵蓋**：支援 NBA、MLB、CPBL、NPB、英超 / 歐冠、NHL、LoL 電競等公開盤口。

---

## 📁 目錄結構

```text
sportsbet_agent/
├── README.md                          # 本說明文件
├── config.json                        # 本地設定 (Telegram 通知與代理節點，未入版控)
├── config.example.json                # 設定檔範本
├── proxy_config.py                    # 澳洲出口代理偵測與只讀 Telegram 發送輔助
├── query_sportsbet.py                 # 全球種即時盤口只讀查詢器
├── market_comparator.py               # 跨平台事件對齊與參考工具
├── test_sportsbet_connection.py       # 澳洲代理連通度測試工具
├── fetch_sportsbet_baseball_odds.py   # 棒球盤口查詢腳本 (MLB / CPBL)
└── fetch_sportsbet_lol_odds.py        # 英雄聯盟盤口查詢腳本 (LoL)
```

---

## 🚀 常用測試指令

```bash
# 驗證澳洲出口代理與連線狀態
python sportsbet_agent/test_sportsbet_connection.py

# 只讀查詢 Sportsbet 即時 NBA 盤口
python sportsbet_agent/query_sportsbet.py "nba"

# 執行 7 平台比價雷達單次採集
python -m radar.collector --once
```

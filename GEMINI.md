# 7 平台只讀量化比價與 +EV 雷達｜專案長期工作流規範

本專案為 **M4（開發端）↔ GitHub (`george770131/sportsbet-odds-analysis`) ↔ M1 Mac mini（24/7 主力生產主機）** 雙機共用專案。無論在哪一台電腦啟動 Antigravity，都必須嚴格遵守以下規範。

## 1. 核心系統邊界（不可破壞）
- **純淨只讀（Read-Only）**：嚴禁重新引入任何自動下注、帳號登入、Cookie/LocalStorage 同步或單筆下注金額控制。使用者透過網站查看比較結果後，自行手動至台灣運彩或澳洲 Sportsbet 下單。
- **7 平台架構**：
  - **5 家國際參考指標**：Polymarket、Kalshi、Pinnacle（免 API Key 公開盤口）、Betfair Exchange (AU)、Bet365（經 Oddsportal 線路），各自獨立以冪次法（Power Method）去水後加權計算真實勝率共識，並標註 `有效參考家數：X/5`（允許 1/5~5/5 皆納入比價）。
  - **2 家可投注目標盤口**：台灣運彩 (TSL) 與澳洲 Sportsbet。台灣運彩非單場（需串關）盤口出現 +EV 時照常顯示，並標註 `⚠️ 需串關`。
- **Telegram +EV 即時推播規範**：
  - **有效參考家數門檻**：僅當 `有效參考家數 >= 3/5` 時才觸發 Telegram 訊息推播（避免 1/5 或 2/5 樣本過少產生雜訊）。
  - **台彩單場嚴格過濾**：台灣運彩需串關（`⚠️ 需串關` / `single_game_allowed == False`）之盤口一律不發送 Telegram 訊息（保留於網頁端供手動查看）；台彩僅在開放「單場可下」時才允許推播。澳洲 Sportsbet 因本身可直接單場下注不受此限。
- **網頁 UI 規範**：維持 **亮色系（Bright / Light Mode `#F8FAFC` / `#FFFFFF`）Mobile-First 手機優先版面**。展開明細表須同時包含 5 家參考指標與 2 家可投注盤口（共 7 列），欄位標題為「平台來源｜原始賠率｜水錢%｜去水勝率」。
- **反爬蟲與安全合規**：禁止對 `sportslottery.com.tw` 或任何站點繞過 Cloudflare Turnstile / CAPTCHA 驗證；僅使用公開無驗證閘門的資料來源。

## 2. 雙機開發與自動同步規範（最重要）
M1（`m1` / `192.168.68.118`，專案路徑 `/Users/george/Developer/sportsbet-odds-analysis`）為 24/7 永不關機之主力機，M1 上的 Antigravity 亦直接開啟此資料夾。

### A. 在 M4 電腦修改本專案後（必做收尾）
每當使用者在 M4 請 Agent 修改程式、網頁或設定並驗證通過後，**不需使用者額外提醒，應主動執行以下同步閉環**，確保 M1 永遠維持最新版本：
1. 確認工作區無敏感機密檔案（絕不可追蹤 `sportsbet_agent/config.json` 或 `data/*.db*`）。
2. 檢查遠端是否有 M1 端先前推上去的更新，並提交本次修改：
   ```bash
   git pull --rebase origin main
   git add -A
   git commit -m "<清楚的中文或英文修改摘要>"
   ```
3. 執行一鍵安全部署腳本（自動 push 至 GitHub `main`、通知 M1 `git pull` 並熱重啟服務）：
   ```bash
   ./deploy/deploy_to_m1.sh
   ```
   - ⚠️ 除非明確需要重新產生新網址，否則 **不要重啟 `odds-tunnel`**，保留現有 Cloudflare Tunnel 網址給手機持續使用。

### B. 在 M1 電腦修改本專案時（開工與收尾）
1. **開始修改前**：先執行 `git pull --rebase origin main`，確保取得 M4 最新推上來的版本。
2. **修改並驗證完成後**：
   ```bash
   export PATH=/opt/homebrew/bin:/usr/local/bin:$PATH
   pm2 restart odds-collector odds-web
   git add -A && git commit -m "<修改摘要>" && git push origin main
   ```

## 3. M1 常駐架構備忘
- **PM2 進程**：`odds-collector`（每 120 秒採集 + 出現正 +EV 即時推送完整 7 盤比價至 Telegram）、`odds-web`（FastAPI 監聽 `127.0.0.1:8501`）、`odds-tunnel`（Cloudflare Quick Tunnel 並在啟動時自動將網址發送至 Telegram）。
- **開機防護**：上述三個服務已登錄於 M1 的 `~/Scripts/pm2_boot_guard.sh` 與 `pm2 save`。
- **澳洲代理**：M1 本機透過 `http://127.0.0.1:8888`（Surfshark AU Docker 容器）直連；M4 則自動使用 `http://192.168.68.118:8888`。

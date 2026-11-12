---
name: m1-sync-deploy
description: >-
  Use this skill whenever modifying, testing, syncing, or deploying the 7-platform
  read-only odds radar project between M4 MacBook, GitHub (main), and M1 Mac mini
  (24/7 PM2 + Cloudflare Tunnel), or when checking M1 scraper/proxy/tunnel health.
---

# M4 ↔ GitHub ↔ M1 雙機同步與 24/7 維運標準流程

此專案同時在 **M4（開發機：`/Users/george/Desktop/賭盤分析`）** 與 **M1（主力生產機：`~/Developer/sportsbet-odds-analysis`）** 運作，透過 `git@github.com:george770131/sportsbet-odds-analysis.git`（SSH Deploy Key 免密碼）進行雙向版本同步。

## 情境一：在 M4 改完功能 → 同步至 GitHub 與 M1（標準閉環）

1. **本機測試驗證**：使用 `.venv/bin/python` 執行對應單元測試、採集器驗證（`python -m radar.collector --once`）或網頁檢查。
2. **確認無敏感資料被追蹤**：
   - `git status -s` 檢查絕對不能出現 `sportsbet_agent/config.json` 或 `data/*.db*`。
3. **提交並執行一鍵同步**：
   ```bash
   git pull --rebase origin main
   git add -A
   git commit -m "chore/feat/fix: <修改內容>"
   ./deploy/deploy_to_m1.sh
   ```
   - `deploy_to_m1.sh` 會自動拉取遠端、推上 `origin/main`、確保 M1 有本地 `config.json`、在 M1 執行 `git pull --rebase` 與依賴檢查，並僅熱重啟 `odds-collector` 與 `odds-web`（**保留原 `odds-tunnel` 網址不斷線**）。
   - 若刻意要換新 Tunnel 網址並推播 Telegram，才改跑 `./deploy/deploy_to_m1.sh --restart-tunnel`。

## 情境二：在 M1 直接改功能 → 套用生效並推回 GitHub

1. **改前先對齊**：
   ```bash
   cd ~/Developer/sportsbet-odds-analysis
   git pull --rebase origin main
   ```
2. **改完套用 PM2（保留 Tunnel 網址）**：
   ```bash
   export PATH=/opt/homebrew/bin:/usr/local/bin:$PATH
   pm2 restart odds-collector odds-web
   ```
3. **推回 GitHub 供 M4 下次開機拉取**：
   ```bash
   git add -A && git commit -m "feat/fix: <修改內容>" && git push origin main
   ```

## 情境三：M1 常見維運與健康檢查

- **檢查 M1 服務狀態與最近日誌**：
  ```bash
  ssh m1 "export PATH=/opt/homebrew/bin:/usr/local/bin:\$PATH && pm2 list && tail -n 20 ~/.pm2/logs/odds-collector-out.log ~/.pm2/logs/odds-web-error.log"
  ```
- **查詢目前 M1 正在使用的 Cloudflare Tunnel 網址**：
  ```bash
  ssh m1 "grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' ~/.pm2/logs/odds-tunnel-out.log | tail -n 1"
  ```
- **檢查 M1 澳洲 Surfshark 出口代理**：
  ```bash
  ssh m1 "curl -s --max-time 4 -x http://127.0.0.1:8888 https://ipinfo.io/json"
  ```

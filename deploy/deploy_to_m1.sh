#!/usr/bin/env bash
set -euo pipefail

# 透過 GitHub (main) 安全雙向同步並重啟 M1 服務（取代單向 rsync --delete，避免覆蓋 M1 上的開發修改）
M1_HOST="${M1_HOST:-m1}"
M1_DIR="${M1_DIR:-~/Developer/sportsbet-odds-analysis}"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESTART_TUNNEL="${1:-}"

cd "${LOCAL_DIR}"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ M4 工作區尚有未提交的變更，請先執行 git add / git commit 後再部署："
  git status -s
  exit 1
fi

echo "🔄 從 GitHub (origin/main) 同步最新進度至 M4..."
git pull --rebase origin main
git push origin main

echo "🔐 確認 M1 本地 config.json 存在（不經由 GitHub）..."
if ! ssh "${M1_HOST}" "test -s ${M1_DIR}/sportsbet_agent/config.json"; then
  scp "${LOCAL_DIR}/sportsbet_agent/config.json" "${M1_HOST}:${M1_DIR}/sportsbet_agent/config.json"
fi

echo "📥 在 M1 拉取最新程式碼並檢查依賴套件..."
ssh "${M1_HOST}" "export PATH=/opt/homebrew/bin:/usr/local/bin:\$PATH && \
  cd ${M1_DIR} && \
  git pull --rebase origin main && \
  ([ -d .venv ] || /usr/bin/python3 -m venv .venv) && \
  ./.venv/bin/pip install -q -r requirements.txt && \
  chmod +x deploy/run_tunnel_notify.sh deploy/deploy_to_m1.sh"

if [[ "${RESTART_TUNNEL}" == "--restart-tunnel" ]]; then
  echo "♻️ 重啟 M1 全部 3 個 PM2 服務（含 Tunnel 新網址推播）..."
  ssh "${M1_HOST}" "export PATH=/opt/homebrew/bin:/usr/local/bin:\$PATH && pm2 restart odds-collector odds-web odds-tunnel && pm2 save"
else
  echo "♻️ 熱重啟 M1 核心服務 (odds-collector, odds-web)，保留現有 Tunnel 網址..."
  ssh "${M1_HOST}" "export PATH=/opt/homebrew/bin:/usr/local/bin:\$PATH && pm2 restart odds-collector odds-web && pm2 save"
fi

echo "✅ GitHub 雙向同步與 M1 熱部署完成！"

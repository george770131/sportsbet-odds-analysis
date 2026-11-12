#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${PROJECT_DIR}/sportsbet_agent/config.json"
CLOUDFLARED_BIN="$(command -v cloudflared || echo "/opt/homebrew/bin/cloudflared")"
PORT="${RADAR_PORT:-8501}"

if [[ ! -x "${CLOUDFLARED_BIN}" ]]; then
  echo "❌ 找不到 cloudflared 執行檔: ${CLOUDFLARED_BIN}" >&2
  exit 1
fi

echo "🚀 啟動 Cloudflare Quick Tunnel 轉發本機 http://127.0.0.1:${PORT} ..."

notified=0
"${CLOUDFLARED_BIN}" tunnel --no-autoupdate --url "http://127.0.0.1:${PORT}" 2>&1 | while IFS= read -r line; do
  echo "${line}"
  if [[ "${notified}" -eq 0 ]] && [[ "${line}" =~ (https://[a-zA-Z0-9-]+\.trycloudflare\.com) ]]; then
    tunnel_url="${BASH_REMATCH[1]}"
    notified=1
    echo "✅ 取得 Cloudflare Tunnel 網址: ${tunnel_url}"
    "${PROJECT_DIR}/.venv/bin/python" - "${CONFIG_FILE}" "${tunnel_url}" <<'PY' || true
import json, sys, urllib.parse, urllib.request
cfg_path, url = sys.argv[1], sys.argv[2]
with open(cfg_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)
token = cfg.get("telegram_bot_token", "")
chat_id = cfg.get("allowed_chat_id", "")
if token and chat_id:
    msg = (
        "🌐 <b>7盤定量比價雷達已上線 (M1 24/7)</b>\n\n"
        f"📱 手機直接點開：<a href=\"{url}\">{url}</a>\n\n"
        "💡 可在手機瀏覽器選擇「加到主畫面」，隨時單手查閱 +EV 盤口。"
    )
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}).encode()
    urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST"), timeout=10)
PY
  fi
done

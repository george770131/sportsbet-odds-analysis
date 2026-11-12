#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "==================================================="
echo "  [7盤定量比價雷達] 正在為您啟動 FastAPI 亮色手機版網站..."
echo "  網址: http://localhost:8501"
echo "==================================================="

# 若本地尚未有快取資料，先快速採集 API 來源讓首頁立即有盤口
if [ ! -f "$DIR/data/radar_master.db" ]; then
    echo "📡 首次啟動，正在預熱採集即時盤口..."
    "$DIR/.venv/bin/python" -m radar.collector --once --fast || true
fi

(sleep 2 && open "http://localhost:8501") &

exec "$DIR/.venv/bin/uvicorn" web.app:app --host 0.0.0.0 --port 8501

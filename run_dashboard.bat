@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title 4-Source Odds Analytics Terminal

echo ===================================================
echo   [Sports Betting Quantitative Analytics Terminal]
echo   Starting Streamlit Web Dashboard...
echo   Url: http://localhost:8501
echo ===================================================

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.headless false
) else (
    python -m streamlit run app.py --server.port 8501 --server.headless false
)

pause

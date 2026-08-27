@echo off
chcp 65001 >nul
echo ===================================================
echo 🏆 正在啟動 Sportsbet & Oddsportal 賭盤智能分析系統...
echo ===================================================

set PYTHON_EXE=C:\Users\qazx5\AppData\Local\Programs\Python\Python311\python.exe

if not exist "%PYTHON_EXE%" (
    echo [!] 找不到指定的 Python 路徑，嘗試使用系統 python...
    set PYTHON_EXE=python
)

echo [*] 正在開啟 Streamlit 網頁伺服器...
echo [*] 瀏覽器將自動開啟 http://localhost:8501
echo [*] 若未自動開啟，請在瀏覽器網址列輸入: http://localhost:8501
echo ===================================================

"%PYTHON_EXE%" -m streamlit run app.py --server.port 8501 --server.headless false

pause

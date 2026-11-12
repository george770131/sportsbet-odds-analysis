#!/usr/bin/env python3
"""
Sportsbet 澳洲連線與反爬繞過獨立測試腳本 (test_sportsbet_connection.py)
-----------------------------------------------------------------------------
功能：
1. 檢驗當前出口 IP 是否為澳洲 (AU) 與相關地理位置 (City/ISP)
2. 支援注入 Surfshark 澳洲 SOCKS5 / HTTP Proxy 或直接本機 VPN 測試
3. 搭載 Playwright Stealth 擬真瀏覽器反爬特徵混淆
4. 測試連線至 https://www.sportsbet.com.au
5. 判斷是否成功突破「Sportsbet Location Error」與 Akamai/Cloudflare 檢測
6. 截圖儲存至本地 (sportsbet_test_result.png) 作為實體驗證
-----------------------------------------------------------------------------
"""

import sys
import json
import time
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

BASE_DIR = Path(__file__).resolve().parent
SCREENSHOT_PATH = BASE_DIR / "sportsbet_test_result.png"

def run_test(proxy_server: str = None, proxy_user: str = None, proxy_pass: str = None):
    print("=" * 65)
    print("🇦🇺 Sportsbet 澳洲連線與反爬繞過獨立驗證程式")
    print("=" * 65)

    proxy_config = None
    if proxy_server:
        proxy_config = {"server": proxy_server}
        if proxy_user and proxy_pass:
            proxy_config["username"] = proxy_user
            proxy_config["password"] = proxy_pass
        print(f"🌐 已配置代理伺服器: {proxy_server}")
    else:
        print("🌐 未配置獨立代理，將使用當前系統原生出口連線進行檢驗")

    with sync_playwright() as p:
        browser_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--lang=en-AU,en"
        ]

        launch_kwargs = {
            "headless": True,
            "args": browser_args
        }
        if proxy_config:
            launch_kwargs["proxy"] = proxy_config

        print("🚀 啟動 Chromium 瀏覽器核心...")
        browser = p.chromium.launch(**launch_kwargs)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="en-AU",
            timezone_id="Australia/Sydney"
        )
        page = context.new_page()

        # 注入 Playwright Stealth 混淆機制
        try:
            Stealth().apply_stealth_sync(page)
            print("🛡️ 已成功加載 Playwright Stealth 反指紋追蹤引擎")
        except Exception as e:
            print(f"⚠️ Stealth 加載警告: {e}")

        # 第一步：檢驗當前出口 IP 與國家
        print("\n[Step 1] 正在向 ipinfo.io 驗證網路出口地理位置...")
        try:
            ip_resp = page.goto("https://ipinfo.io/json", timeout=20000)
            if ip_resp and ip_resp.status == 200:
                ip_data = json.loads(page.inner_text("body"))
                ip = ip_data.get("ip", "Unknown")
                country = ip_data.get("country", "Unknown")
                city = ip_data.get("city", "Unknown")
                org = ip_data.get("org", "Unknown")
                print(f"   • 出口 IP: {ip}")
                print(f"   • 所在國家: {country} ({'✅ 澳洲 AU 符合要求' if country == 'AU' else '❌ 非澳洲出口'})")
                print(f"   • 所在城市: {city}")
                print(f"   • ISP / 機房: {org}")
            else:
                print("   ⚠️ 無法獲取出口 IP 詳細資料")
        except Exception as e:
            print(f"   ⚠️ IP 探測遭遇異常: {e}")

        # 第二步：測試連線 Sportsbet 首頁
        target_url = "https://www.sportsbet.com.au"
        print(f"\n[Step 2] 正在嘗試造訪 Sportsbet 澳洲首頁: {target_url} ...")
        try:
            start_time = time.time()
            resp = page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            elapsed = time.time() - start_time
            status_code = resp.status if resp else "None"
            page_title = page.title()
            current_url = page.url

            print(f"   • HTTP 狀態碼: {status_code} (耗時 {elapsed:.2f} 秒)")
            print(f"   • 頁面標題 (Title): {page_title}")
            print(f"   • 最終跳轉 URL: {current_url}")

            # 等待前端 React / 動態元件渲染
            page.wait_for_timeout(4000)

            # 儲存實體截圖
            page.screenshot(path=str(SCREENSHOT_PATH), full_page=False)
            print(f"   📸 已截圖保存至: {SCREENSHOT_PATH}")

            # 第三步：判定結果
            print("\n[Step 3] 檢測結果診斷:")
            if "Location Error" in page_title or "Location Error" in page.content():
                print("   ❌ 觸發「Sportsbet Location Error」：被判定為非澳洲當地 IP 或代理被辨識。")
                print("   👉 診斷：需要掛上有效的 Surfshark 澳洲節點（SOCKS5 / WireGuard）。")
            elif status_code == 200 and "Sportsbet" in page_title:
                print("   🎉 恭喜！成功突破地理封鎖與反爬防禦！Sportsbet 首頁已正常渲染！")
            elif status_code == 403:
                print("   ❌ HTTP 403 拒絕訪問 (Akamai / Cloudflare 防火牆阻擋)。")
            else:
                print(f"   ℹ️ 頁面已載入，狀態碼: {status_code}，請檢視截圖確認內容。")

        except Exception as e:
            print(f"   ❌ 連線 Sportsbet 發生例外: {e}")

        browser.close()
        print("\n" + "=" * 65)

if __name__ == "__main__":
    CONFIG_FILE = BASE_DIR / "config.json"
    default_proxy = None
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as _cf:
                default_proxy = json.load(_cf).get("proxy_server")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Sportsbet 澳洲連線測試工具")
    parser.add_argument("--proxy", default=default_proxy, help="SOCKS5 或 HTTP 代理 URL (例: http://127.0.0.1:8888)")
    parser.add_argument("--user", help="Surfshark 服務帳號 (Service Username)")
    parser.add_argument("--password", help="Surfshark 服務密碼 (Service Password)")
    args = parser.parse_args()

    run_test(proxy_server=args.proxy, proxy_user=args.user, proxy_pass=args.password)

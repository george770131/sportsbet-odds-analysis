import asyncio
import json
import sys
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def test_stealth():
    url = "https://www.sportsbet.com.au/betting/baseball/major-league-baseball"
    print(f"[*] 正在使用 Stealth Playwright 連線: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-position=0,0",
                "--ignore-certificate-errors",
                "--ignore-certificate-errors-spki-list",
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="en-AU",
            timezone_id="Australia/Sydney"
        )
        page = await context.new_page()
        await stealth_async(page)

        # 監聽網路請求
        api_responses = []
        async def handle_response(response):
            if "sportsbook" in response.url or "events" in response.url or "competitions" in response.url or "graph" in response.url:
                try:
                    ct = response.headers.get("content-type", "")
                    if "json" in ct:
                        body = await response.json()
                        api_responses.append((response.url, body))
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            resp = await page.goto(url, wait_until="networkidle", timeout=30000)
            title = await page.title()
            print(f"頁面狀態: {resp.status if resp else 'None'}, 標題: {title}")

            # 抓取頁面所有文字與賽事元素
            text_content = await page.evaluate("() => document.body.innerText")
            print(f"頁面文字長度: {len(text_content)}")
            print("頁面內容前 500 字元:")
            print(text_content[:500])
            
            print(f"\n捕獲 API 響應數: {len(api_responses)}")
            for u, d in api_responses:
                print(f"API: {u[:100]}")

        except Exception as e:
            print(f"[!] 錯誤: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_stealth())

import asyncio
import json
import re
import sys
from playwright.async_api import async_playwright

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def test_oddsportal_playwright():
    url = "https://www.oddsportal.com/baseball/usa/mlb/"
    print(f"[*] 正在使用 Playwright 開啟 Oddsportal: {url}")
    
    ajax_calls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        async def handle_response(response):
            # Capture JSON and feed calls
            if "feed" in response.url or "ajax" in response.url or "odds" in response.url:
                try:
                    text = await response.text()
                    ajax_calls.append((response.url, text[:500]))
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(4000)

            # Extract the rendered odds table from DOM directly
            rows_data = await page.evaluate("""() => {
                const results = [];
                // Look for event rows in the rendered table
                const rows = document.querySelectorAll('div[class*="eventRow"], div[class*="border-b border-gray"], div[data-v-e6]');
                rows.forEach(r => {
                    const text = r.innerText.replace(/\\n+/g, ' | ');
                    if (text && text.length > 5) {
                        results.push(text);
                    }
                });
                return results;
            }""")

            print(f"找到 {len(rows_data)} 行 DOM 表格資料:")
            for r in rows_data[:15]:
                print("  Row:", r)

            print(f"\n捕獲 {len(ajax_calls)} 個 AJAX/Feed 請求:")
            for u, t in ajax_calls[:10]:
                print(f"  URL: {u}")
                print(f"  Snippet: {t[:150]}")

        except Exception as e:
            print(f"[!] 錯誤: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_oddsportal_playwright())

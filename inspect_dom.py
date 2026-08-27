import asyncio
import sys
from playwright.async_api import async_playwright

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def inspect_oddsportal_dom():
    url = "https://www.oddsportal.com/baseball/usa/mlb/"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            # Get main inner text
            main_text = await page.evaluate("() => document.querySelector('main') ? document.querySelector('main').innerText : document.body.innerText")
            print("Main text length:", len(main_text))
            print("\n--- 渲染內容預覽 ---")
            lines = [l.strip() for l in main_text.split("\n") if l.strip()]
            for l in lines[:60]:
                print(l)

        except Exception as e:
            print(f"[!] 錯誤: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_oddsportal_dom())

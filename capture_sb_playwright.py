import asyncio
import sys
from playwright.async_api import async_playwright

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def test_sportsbet_dom():
    url = "https://www.sportsbet.com.au/betting/baseball/major-league-baseball"
    print(f"[*] Loading Sportsbet with Playwright: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-AU",
            timezone_id="Australia/Sydney"
        )
        page = await context.new_page()
        
        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            print(f"Response status: {resp.status if resp else 'None'}")
            await page.wait_for_timeout(6000)
            
            # Print page title
            print("Page title:", await page.title())
            
            # Extract match cards from DOM
            text = await page.evaluate("() => document.body.innerText")
            print(f"Body text length: {len(text)}")
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            print("First 40 lines:")
            for l in lines[:40]:
                print("  ", l)
                
        except Exception as e:
            print(f"[!] Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_sportsbet_dom())

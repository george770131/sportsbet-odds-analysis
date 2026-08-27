import json
import sys
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def test_sync_stealth():
    url = "https://www.sportsbet.com.au/betting/baseball/major-league-baseball"
    print(f"[*] 正在連線: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-AU",
            timezone_id="Australia/Sydney"
        )
        page = context.new_page()
        stealth = Stealth()
        stealth.apply_stealth_sync(page)

        try:
            resp = page.goto(url, wait_until="networkidle", timeout=30000)
            print(f"Status: {resp.status if resp else 'None'}, Title: {page.title()}")
            text = page.inner_text("body")
            print(f"Body text length: {len(text)}")
            print("Content preview:")
            print(text[:600])
        except Exception as e:
            print(f"[!] Exception: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_sync_stealth()

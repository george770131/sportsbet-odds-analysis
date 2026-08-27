import asyncio
import sys
from playwright.async_api import async_playwright

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def inspect_full_table():
    url = "https://www.oddsportal.com/baseball/usa/mlb/"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        main_text = await page.evaluate("() => document.body.innerText")
        lines = [l.strip() for l in main_text.split("\n") if l.strip()]
        
        for idx, l in enumerate(lines):
            if any(t in l for t in ["Angels", "Guardians", "Yankees", "Dodgers", "Tigers", "Braves", "Red Sox"]):
                print(f"\n[Line {idx}] -> {l}")
                print("Followed by next 8 lines:")
                for n in lines[idx+1: idx+9]:
                    print("  ->", n)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_full_table())

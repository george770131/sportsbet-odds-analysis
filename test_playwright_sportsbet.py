import asyncio
import json
import sys
from playwright.async_api import async_playwright

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def scrape_sportsbet_mlb():
    url = "https://www.sportsbet.com.au/betting/baseball/major-league-baseball"
    print(f"[*] 正在使用 Playwright 開啟: {url}")
    
    captured_events = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-AU",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        # 監聽網路請求，補捉 Sportsbet 的 JSON API 資料
        async def handle_response(response):
            if "sportsbook" in response.url or "events" in response.url or "graphql" in response.url or "competitions" in response.url:
                try:
                    if "application/json" in response.headers.get("content-type", ""):
                        data = await response.json()
                        captured_events.append((response.url, data))
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(5000) # 等待資料非同步載入

            # 從瀏覽器內部 Window 物件提取 Redux 或 Apollo State
            window_state = await page.evaluate("""() => {
                const results = {};
                if (window.__PRELOADED_STATE__) {
                    results.preloaded = window.__PRELOADED_STATE__;
                }
                // 檢查頁面中渲染的所有賽事卡片與賠率
                const cards = [];
                document.querySelectorAll('[data-automation-id="event-card"], [data-automation-id="competition-event"], div[class*="eventCard"], div[class*="event-card"]').forEach(el => {
                    cards.push(el.innerText);
                });
                results.cards = cards;
                return results;
            }""")

            print(f"[✓] 網頁載入成功！標題: {await page.title()}")
            print(f"補捉到 {len(captured_events)} 個 API 響應")
            
            # 檢查 window state 中的 sportsbook entities
            sb_entities = window_state.get("preloaded", {}).get("entities", {}).get("sportsbook", {})
            events_dict = sb_entities.get("events", {})
            markets_dict = sb_entities.get("markets", {})
            outcomes_dict = sb_entities.get("outcomes", {})
            
            print(f"Sportsbook 實體 -> Events: {len(events_dict)}, Markets: {len(markets_dict)}, Outcomes: {len(outcomes_dict)}")

            if events_dict:
                for eid, ev in list(events_dict.items())[:10]:
                    print(f"  賽事: {ev.get('name') or ev.get('title')}, 時間: {ev.get('startTime')}")
                    # 查看關聯 market
                    for mid in ev.get("marketIds", []):
                        m = markets_dict.get(str(mid))
                        if m:
                            print(f"    盤口: {m.get('name')}")
                            for oid in m.get("outcomeIds", []):
                                o = outcomes_dict.get(str(oid))
                                if o:
                                    print(f"      選項: {o.get('name')} @ 賠率: {o.get('price', {}).get('decimal') or o.get('price')}")

            # 打印捕獲的 API 回應摘要
            for u, d in captured_events:
                print(f"API URL: {u[:90]}")
                if isinstance(d, dict):
                    print(f"  Keys: {list(d.keys())}")
                    if "events" in d:
                        print(f"  Events inside: {len(d['events'])}")

            if window_state.get("cards"):
                print(f"\n找到 {len(window_state['cards'])} 個 DOM 卡片:")
                for c in window_state['cards'][:3]:
                    print(f"--- 卡片 ---\n{c[:200]}")

        except Exception as e:
            print(f"[!] Playwright 執行錯誤: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_sportsbet_mlb())

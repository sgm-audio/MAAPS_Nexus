import asyncio
import os
from playwright.async_api import async_playwright
from interceptor import SunoInterceptor
from pusher import WebhookPusher
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def scroll_page(page, duration_seconds: int = 60):
    """
    Scrolls the page periodically to trigger infinite scroll.
    """
    print("Starting scroll loop...")
    for _ in range(duration_seconds // 2):
        await page.evaluate("window.scrollBy(0, 800)")
        await asyncio.sleep(2)
        # Randomize scroll slightly to look more human?
        # For now, simple scroll is fine.

async def main():
    print("Starting Suno Hydra Scraper...")
    
    # Initialize components
    interceptor = SunoInterceptor()
    # If no webhook URL is set, we will just log the output (Dry Run Mode effectively)
    webhook_url = os.getenv("N8N_WEBHOOK_URL")
    pusher = WebhookPusher(webhook_url) if webhook_url else None
    
    if not webhook_url:
        print("WARNING: N8N_WEBHOOK_URL not set. Running in Dry Run mode (no data push).")

    async with async_playwright() as p:
        # Launch browser (headless by default, set headless=False to debug visually)
        # We use a user agent to look like a real browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )

        page = await context.new_page()

        # Attach interceptor
        page.on("response", interceptor.handle_response)

        # Navigate to Suno Explore
        print("Navigating to https://suno.com/explore...")
        try:
            await page.goto("https://suno.com/explore", timeout=60000)
            print("Page loaded. Waiting for feed...")
            await page.wait_for_timeout(5000) # Give initial load time
        except Exception as e:
            print(f"Navigation failed: {e}")
            await browser.close()
            return

        # Main Loop
        start_time = asyncio.get_event_loop().time()
        # Run for a fixed duration or indefinitely. 
        # For this v1, let's run for 2 minutes then exit, effectively a cron job batch.
        # Or ideally, run until we have X tracks.
        
        MAX_DURATION = 120 # seconds
        print(f"Scraping for {MAX_DURATION} seconds...")

        task = asyncio.create_task(scroll_page(page, MAX_DURATION))
        
        while (asyncio.get_event_loop().time() - start_time) < MAX_DURATION:
            await asyncio.sleep(5)
            
            # Flush buffer every few seconds
            batch = interceptor.get_and_clear_buffer()
            if batch:
                print(f"Processing batch of {len(batch)} tracks...")
                if pusher:
                    await pusher.push_batch(batch)
                else:
                    print(f"Dry Run: Would push {len(batch)} tracks.")
        
        await task
        print("Scrape session finished.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

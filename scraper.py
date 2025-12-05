import asyncio
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class AntigravityScraper:
    """
    The 'Antigravity' class. It floats over anti-bot measures.
    """
    
    def __init__(self):
        self.browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

    async def get_listing_data(self, url):
        """Spins up a stealthy browser to grab the raw HTML and extract key data."""
        print(f"[bold blue]>> Launching Antigravity engine for:[/bold blue] {url}")
        async with async_playwright() as p:
            # Headless=False to look more human if needed, but trying True first for speed if possible.
            # User suggested Headless=False if needed. Let's default to True but keep it configurable if we were to expand.
            # For LBC, sometimes Headless=False is safer. Let's stick to the user's hint or the base code.
            # Base code had headless=True. I'll stick to that but add a comment.
            browser = await p.chromium.launch(headless=False, args=self.browser_args) # Changed to False as LBC is tough
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Handle cookie banner if it exists (generic approach)
                try:
                    # Common LBC cookie button selector (might change, but good to try)
                    await page.click('#didomi-notice-agree-button', timeout=5000)
                except:
                    pass # No banner or different ID

                # Random scroll to trigger lazy loading and look human
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2) 
                
                content = await page.content()
                
                # Basic parsing here to get the price if possible, but the Analyzer will do the heavy lifting
                # We return the full HTML or a structured dict if we want to do some pre-processing.
                # For now, let's return the raw text and let the Brain handle it, 
                # BUT we also want to try to extract the price specifically if it's easy, 
                # to pass it to the analyzer as a fallback/confirmation.
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract Title
                title_tag = soup.find('h1')
                title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
                
                # Extract Price (LBC specific structure often changes). Best-effort extraction.
                price_text = ""
                # Look for price in common places
                price_tag = soup.select_one('[data-qa-id="adview_price"]')
                if price_tag:
                    raw_price = price_tag.get_text(separator=' ', strip=True)
                else:
                    # Fallback: search the entire page text for something that looks like a euro amount
                    raw_price = soup.get_text(separator=' ', strip=True)

                # Helper to clean and extract a numeric price (handles NBSP and thin spaces)
                def extract_price_from_text(s: str) -> str:
                    if not s:
                        return ""
                    # Common NBSP or narrow NBSP characters
                    s = s.replace('\u00A0', ' ').replace('\u202F', ' ').replace('\u2009', ' ')
                    # Try to find patterns like '1 000 €' or '1000€' or '1\u0000 000 €'
                    m = re.search(r"(\d{1,3}(?:[ \.,]\d{3})*(?:[\.,]\d+)?)\s*€", s)
                    if not m:
                        # fallback: any standalone number sequence
                        m = re.search(r"(\d[\d \.,]*)", s)
                    if not m:
                        return ""
                    num = m.group(1)
                    # Remove grouping spaces and non-digit punctuation, keep decimal dot
                    num = num.replace(' ', '').replace('\u00A0', '').replace('\u202F', '')
                    num = num.replace(',', '.')
                    # Strip any trailing non-digit/point
                    num = re.sub(r"[^0-9.]", '', num)
                    return num

                price_text = extract_price_from_text(raw_price)
                
                # Extract Description
                description_tag = soup.select_one('[data-qa-id="adview_description_container"]')
                raw_text = description_tag.get_text(separator='\n', strip=True) if description_tag else soup.get_text(separator=' ', strip=True)
                
                return {
                    "title": title,
                    "price_str": price_text,
                    "raw_text": raw_text[:8000], # Limit for tokens
                    "url": url
                }

            except Exception as e:
                print(f"[bold red]💥 Gravity too heavy (Error): {e}[/bold red]")
                return None
            finally:
                await browser.close()

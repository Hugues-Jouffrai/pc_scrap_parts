import asyncio
from scraper import AntigravityScraper

async def test():
    scraper = AntigravityScraper()
    print("Testing scraper...")
    data = await scraper.get_listing_data("https://www.leboncoin.fr/ad/ordinateurs/3082027877")
    
    if data:
        print(f"\nTitle: {data['title']}")
        print(f"Price: {data['price_str']}€")
        print(f"Description preview: {data['raw_text'][:200]}...")
    else:
        print("Failed to scrape")

if __name__ == "__main__":
    asyncio.run(test())

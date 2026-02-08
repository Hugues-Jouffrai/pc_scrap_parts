import asyncio
import json
import os
import shutil
import time
from datetime import datetime

from scraper import AntigravityScraper
from analyzer import AntigravityAnalyzer

DATA_FILE = "data.js"
BACKUP_DIR = "backups"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds between retries


def load_history():
    if not os.path.exists(DATA_FILE):
        print(f"No {DATA_FILE} found.")
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    json_str = text.replace("window.SCRAP_HISTORY = ", "").strip().rstrip(";")
    try:
        return json.loads(json_str)
    except Exception as e:
        print(f"Failed to parse {DATA_FILE}: {e}")
        return []


def save_history(history):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(f"window.SCRAP_HISTORY = {json.dumps(history, indent=4, ensure_ascii=False)};")


async def fetch_with_retries(scraper, url):
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            data = await scraper.get_listing_data(url)
            if data:
                return True, data, None
            else:
                last_exc = RuntimeError("No data returned")
        except Exception as e:
            last_exc = e
        print(f"    Attempt {attempt} failed for {url}: {last_exc}")
        if attempt < MAX_RETRIES:
            print(f"    Waiting {RETRY_DELAY}s before retrying...")
            await asyncio.sleep(RETRY_DELAY)
    return False, None, last_exc


async def analyze_with_retries(analyzer, data):
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            analysis = analyzer.analyze_profitability(data)
            return True, analysis, None
        except Exception as e:
            last_exc = e
        print(f"    Analysis attempt {attempt} failed: {last_exc}")
        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY)
    return False, None, last_exc


async def reprocess_all():
    history = load_history()
    if not history:
        print("No history entries to reprocess.")
        return

    # Backup
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"data.js.bak.{ts}")
    shutil.copy2(DATA_FILE, backup_file)
    print(f"Backed up {DATA_FILE} -> {backup_file}")

    scraper = AntigravityScraper()
    analyzer = AntigravityAnalyzer()

    total = len(history)
    failures = []

    for idx, entry in enumerate(history):
        url = entry.get("url")
        print(f"[{idx+1}/{total}] Reprocessing: {url}")

        ok, data, err = await fetch_with_retries(scraper, url)
        if not ok:
            print(f"  ERROR: Failed to fetch after retries: {err}")
            failures.append((url, 'fetch', str(err)))
            continue

        ok2, analysis, err2 = await analyze_with_retries(analyzer, data)
        if not ok2:
            print(f"  ERROR: Analysis failed after retries: {err2}")
            failures.append((url, 'analyze', str(err2)))
            continue

        # Update entry fields
        entry["id"] = datetime.now().isoformat()
        entry["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry["url"] = data.get("url", entry.get("url"))
        entry["title"] = data.get("title", entry.get("title"))
        entry["price"] = analysis.get("listing_price", entry.get("price", 0))
        entry["estimated"] = analysis.get("total_estimated_value", entry.get("estimated", 0))
        entry["profit"] = analysis.get("profit_potential", entry.get("profit", 0))
        entry["margin"] = analysis.get("profit_percentage", entry.get("margin", 0))
        entry["verdict"] = analysis.get("verdict", entry.get("verdict", "PASS"))
        entry["parts"] = analysis.get("parts", entry.get("parts", []))
        entry["reasoning"] = analysis.get("reasoning", entry.get("reasoning", ""))

        print(f"  Updated: estimated={entry['estimated']}€, profit={entry['profit']}€, verdict={entry['verdict']}")

        # small pause to be polite
        time.sleep(1)

    # Save updated history
    save_history(history)

    print("Reprocessing complete.")
    if failures:
        print("The following entries failed:")
        for f in failures:
            print(" -", f)
    else:
        print("All entries processed successfully.")


if __name__ == "__main__":
    asyncio.run(reprocess_all())

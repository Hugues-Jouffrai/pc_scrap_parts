import asyncio
import json
import os
import shutil
from datetime import datetime

from scraper import AntigravityScraper
from analyzer import AntigravityAnalyzer

DATA_FILE = "data.js"
BACKUP_DIR = "backups"


def load_history():
    if not os.path.exists(DATA_FILE):
        print(f"No {DATA_FILE} found.")
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    # Expect file like: window.SCRAP_HISTORY = [ ... ];
    json_str = text.replace("window.SCRAP_HISTORY = ", "").strip().rstrip(";")
    try:
        return json.loads(json_str)
    except Exception as e:
        print(f"Failed to parse {DATA_FILE}: {e}")
        return []


def save_history(history):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(f"window.SCRAP_HISTORY = {json.dumps(history, indent=4, ensure_ascii=False)};")


async def reprocess_all():
    history = load_history()
    if not history:
        print("No history entries to reprocess.")
        return

    # Make backup
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"data.js.bak.{ts}")
    shutil.copy2(DATA_FILE, backup_file)
    print(f"Backed up {DATA_FILE} -> {backup_file}")

    scraper = AntigravityScraper()
    analyzer = AntigravityAnalyzer()

    total = len(history)
    for idx, entry in enumerate(history):
        url = entry.get("url")
        print(f"[{idx+1}/{total}] Reprocessing: {url}")
        try:
            data = await scraper.get_listing_data(url)
            if not data:
                print(f"  Failed to fetch data for {url}, skipping.")
                continue
            analysis = analyzer.analyze_profitability(data)

            # Update entry fields in place
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

        except Exception as e:
            print(f"  Error processing {url}: {e}")

    # Save updated history
    save_history(history)
    print(f"Reprocessing complete. Updated {DATA_FILE} (backup at {backup_file}).")


if __name__ == "__main__":
    asyncio.run(reprocess_all())

import json
import os

DATA_FILE = "data.js"

def load_history():
    if not os.path.exists(DATA_FILE):
        print(f"No {DATA_FILE} found.")
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    json_str = text.replace("window.SCRAP_HISTORY = ", "").strip().rstrip(";")
    try:
        history = json.loads(json_str)
        print(f"Loaded {len(history)} entries from {DATA_FILE}")
        for i, entry in enumerate(history, 1):
            print(f"  {i}. {entry.get('url', 'NO URL')}")
        return history
    except Exception as e:
        print(f"Failed to parse {DATA_FILE}: {e}")
        return []

if __name__ == "__main__":
    history = load_history()

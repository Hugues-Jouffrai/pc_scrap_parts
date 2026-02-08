"""
rewrite_cache_schema.py
Ensure `components_cache.csv` has the proper schema including fetcher columns.
- Reads the current CSV.
- Adds `fetcher_estimated_new_eur` and `fetcher_estimated_used_eur` columns if missing.
- If those fields are missing or empty, populate them using `price_fetcher._estimate_price_from_name`.
- If recommended_min/max exist, set `estimated_new_price_eur` to midpoint (keeps existing otherwise).
- Writes the CSV back with the canonical header order.

Run:
    python rewrite_cache_schema.py
"""
from pathlib import Path
import csv
from price_fetcher import _estimate_price_from_name

CACHE = Path("components_cache.csv")

FIELDNAMES = [
    "component_name",
    "category",
    "estimated_new_price_eur",
    "estimated_used_price_eur",
    "recommended_min_eur",
    "recommended_max_eur",
    "fetcher_estimated_new_eur",
    "fetcher_estimated_used_eur",
    "last_updated",
    "source",
]


def main():
    if not CACHE.exists():
        print("No cache found.")
        return

    rows = []
    with CACHE.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    out = []
    for r in rows:
        name = r.get("component_name")
        rec_min = r.get("recommended_min_eur")
        rec_max = r.get("recommended_max_eur")

        # compute fetcher estimate if missing
        fetch_new = r.get("fetcher_estimated_new_eur")
        fetch_used = r.get("fetcher_estimated_used_eur")
        if not fetch_new:
            try:
                est = float(_estimate_price_from_name(name))
                fetch_new = str(est)
                fetch_used = str(round(est * (1 - 0.35), 2))
            except Exception:
                fetch_new = ""
                fetch_used = ""

        # if recommended range exists, set main estimated to midpoint
        est_new = r.get("estimated_new_price_eur")
        if rec_min and rec_max:
            try:
                rec_min_f = float(rec_min)
                rec_max_f = float(rec_max)
                midpoint = (rec_min_f + rec_max_f) / 2.0
                est_new = str(round(midpoint, 2))
                est_used = str(round(midpoint * (1 - 0.35), 2))
            except Exception:
                est_used = r.get("estimated_used_price_eur") or ""
        else:
            est_used = r.get("estimated_used_price_eur") or ""

        out.append({
            "component_name": r.get("component_name", ""),
            "category": r.get("category", ""),
            "estimated_new_price_eur": est_new or "",
            "estimated_used_price_eur": est_used or "",
            "recommended_min_eur": rec_min or "",
            "recommended_max_eur": rec_max or "",
            "fetcher_estimated_new_eur": fetch_new or "",
            "fetcher_estimated_used_eur": fetch_used or "",
            "last_updated": r.get("last_updated", ""),
            "source": r.get("source", ""),
        })

    # Write back
    with CACHE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(out)

    print(f"Rewrote {len(out)} rows with canonical schema.")


if __name__ == '__main__':
    main()

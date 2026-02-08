"""
bulk_update_cache.py
Bulk update `components_cache.csv` entries:
- If `recommended_min_eur` and `recommended_max_eur` exist, set `estimated_new_price_eur` to midpoint and recompute used price.
- Otherwise, use `price_fetcher._estimate_price_from_name` to compute a reasonable `estimated_new_price_eur` and recompute used price.

This script updates the CSV in-place using `price_fetcher.save_cache_entry` so fuzzy-merge logic is preserved.

Usage:
    python bulk_update_cache.py

"""
import csv
from pathlib import Path
from price_fetcher import (
    save_cache_entry,
    _estimate_price_from_name,
    get_all_cached_components,
    ensure_cache_exists,
)

CACHE = Path("components_cache.csv")


def main():
    ensure_cache_exists()
    rows = get_all_cached_components()
    if not rows:
        print("No cached components to update.")
        return

    updated = 0
    for r in rows:
        name = r.get("component_name")
        category = r.get("category") or "Other"
        rec_min = r.get("recommended_min_eur")
        rec_max = r.get("recommended_max_eur")

        # Compute fetcher estimate for informational column
        try:
            fetcher_est = float(_estimate_price_from_name(name))
        except Exception:
            fetcher_est = None

        if rec_min and rec_max:
            try:
                rec_min_f = float(rec_min)
                rec_max_f = float(rec_max)
                midpoint = (rec_min_f + rec_max_f) / 2.0
                # Save using save_cache_entry so it updates last_updated and used price
                save_cache_entry(
                    name,
                    category,
                    round(midpoint, 2),
                    source=r.get("source", "pcprice.watch"),
                    recommended_min_eur=rec_min_f,
                    recommended_max_eur=rec_max_f,
                    fetcher_estimated_new_eur=fetcher_est,
                    fetcher_estimated_used_eur=(round(fetcher_est * (1 - 0.35), 2) if fetcher_est else None),
                )
                updated += 1
                continue
            except Exception:
                pass

        # Fallback: re-estimate from name
        est = _estimate_price_from_name(name)
        save_cache_entry(
            name,
            category,
            est,
            source=r.get("source", "estimate"),
            fetcher_estimated_new_eur=est,
            fetcher_estimated_used_eur=round(est * (1 - 0.35), 2),
        )
        updated += 1

    print(f"Updated {updated} cache entries.")


if __name__ == '__main__':
    main()

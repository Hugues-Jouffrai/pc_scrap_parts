"""
audit_cache.py
Simple script to audit `components_cache.csv` and list rows where
our `estimated_new_price_eur` deviates from the recommended midpoint by more than a threshold.

Usage:
    python audit_cache.py [threshold_percent]

Example:
    python audit_cache.py 30
"""

import csv
import sys
from pathlib import Path

CACHE = Path("components_cache.csv")


def load_cache():
    if not CACHE.exists():
        print("No components_cache.csv found in current directory.")
        sys.exit(1)
    with CACHE.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def audit(threshold_percent: float = 30.0):
    rows = load_cache()
    threshold = threshold_percent / 100.0
    flagged = []

    for r in rows:
        try:
            rec_min = r.get("recommended_min_eur")
            rec_max = r.get("recommended_max_eur")
            if not rec_min or not rec_max:
                continue
            rec_min_f = float(rec_min)
            rec_max_f = float(rec_max)
            if rec_min_f <= 0 or rec_max_f <= 0:
                continue
            midpoint = (rec_min_f + rec_max_f) / 2.0
            est = float(r.get("estimated_new_price_eur") or 0)
            if midpoint == 0:
                continue
            diff = abs(midpoint - est) / midpoint
            if diff > threshold:
                flagged.append((r, midpoint, est, diff))
        except Exception:
            continue

    if not flagged:
        print(f"No rows deviate more than {threshold_percent}% from recommended midpoint.")
        return

    print(f"Rows deviating more than {threshold_percent}% (count: {len(flagged)}):\n")
    for r, midpoint, est, diff in flagged:
        name = r.get("component_name")
        cat = r.get("category")
        src = r.get("source")
        rec_range = f"{r.get('recommended_min_eur')} - {r.get('recommended_max_eur')}"
        print(f"- {name} [{cat}] (source: {src})")
        print(f"  recommended midpoint: €{midpoint:.2f}, estimated: €{est:.2f}, deviation: {diff*100:.1f}%")
        print(f"  recommended range: {rec_range}")
        print()


if __name__ == '__main__':
    thr = 30.0
    if len(sys.argv) > 1:
        try:
            thr = float(sys.argv[1])
        except Exception:
            pass
    audit(thr)

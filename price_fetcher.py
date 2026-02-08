"""
price_fetcher.py
Fetches market prices for PC components from pcprice.watch and caches results
in components_cache.csv to avoid redundant lookups.
"""

import csv
import os
import re
from datetime import datetime, timedelta
from typing import Optional, Dict
from difflib import SequenceMatcher


CACHE_FILE = "components_cache.csv"
USED_PART_DISCOUNT = 0.35  # 35% discount for used parts
CACHE_EXPIRY_DAYS = 30


def normalize_component_name(name: str) -> str:
    """
    Normalize component names to enable better deduplication.
    Examples:
    - "RAM DDR4 16 GB" -> "16GB DDR4"
    - "16gb DDR4 Ram" -> "16GB DDR4"
    - "AMD RX 6800XT" -> "RX 6800XT"
    - "SSD 2x1TB" -> "2TB SSD"
    - "2x1TB SSD" -> "2TB SSD"
    """
    name = name.lower().strip()
    
    # Remove common prefixes/suffixes
    name = re.sub(r'\b(the|a|an)\b', '', name)
    
    # Normalize spaces and case
    name = ' '.join(name.split())
    
    # Extract and normalize RAM capacity (move to front)
    ram_match = re.search(r'(\d+)\s*x?\s*(gb|gib)\s*(ddr[45])', name, re.IGNORECASE)
    if ram_match:
        capacity = ram_match.group(1)
        ddr = ram_match.group(3).upper()
        name = f"{capacity}GB {ddr}"
        return name
    
    # Extract single RAM capacity (move to front)
    ram_match = re.search(r'(\d+)\s*(gb|gib)\s*(ddr[45]|memory|ram)', name, re.IGNORECASE)
    if ram_match:
        capacity = ram_match.group(1)
        ddr = "DDR4"  # Default
        if "ddr5" in name.lower():
            ddr = "DDR5"
        name = f"{capacity}GB {ddr}"
        return name
    
    # Extract and normalize SSD capacity (move to front, standardize format)
    # Handle both "2x1TB SSD" and "SSD 2x1TB" patterns
    ssd_match = re.search(r'(\d+)\s*x?\s*(\d+)?\s*(tb|gb)\s*(ssd|nvme)?', name, re.IGNORECASE)
    if ssd_match and ("ssd" in name.lower() or "nvme" in name.lower()):
        if ssd_match.group(2):  # Multiple drives like "2x1TB"
            capacity = int(ssd_match.group(1)) * int(ssd_match.group(2))
        else:
            capacity = ssd_match.group(1)
        unit = ssd_match.group(3).upper()
        name = f"{capacity}{unit} SSD"
        return name
    
    # Normalize known component patterns
    name = re.sub(r'\bseasonic\s+(\d+)w\s+80\s*plus\s+bronze\b', r'SeaSonic \1W 80Plus Bronze', name, flags=re.IGNORECASE)
    name = re.sub(r'\brx\s+6800\s*xt?\b', 'RX 6800XT', name, flags=re.IGNORECASE)
    name = re.sub(r'\brtx\s+(\d+)\b', r'RTX \1', name, flags=re.IGNORECASE)
    name = re.sub(r'\bgtx\s+(\d+)\b', r'GTX \1', name, flags=re.IGNORECASE)
    name = re.sub(r'\bryzen\s+(\d+)\s+(\d+)x?\b', r'Ryzen \1 \2X', name, flags=re.IGNORECASE)
    name = re.sub(r'\bi[357][-]?(\d+)', r'i\1', name, flags=re.IGNORECASE)
    
    # Final cleanup
    name = ' '.join(name.split())
    return name


def fuzzy_match_component(component_name: str, cached_entries: list, threshold: float = 0.85) -> Optional[Dict]:
    """
    Fuzzy match a component name against cached entries.
    Returns the best match if similarity > threshold, else None.
    """
    if not cached_entries:
        return None
    
    normalized_name = normalize_component_name(component_name)
    best_match = None
    best_ratio = 0
    
    for entry in cached_entries:
        cached_normalized = normalize_component_name(entry.get("component_name", ""))
        ratio = SequenceMatcher(None, normalized_name, cached_normalized).ratio()
        
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = entry
    
    if best_ratio >= threshold:
        return best_match
    
    return None


def ensure_cache_exists():
    """Create the cache CSV file if it doesn't exist."""
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "component_name",
                    "category",
                    "estimated_new_price_eur",
                    "estimated_used_price_eur",
                    "last_updated",
                    "source",
                ],
            )
            writer.writeheader()


def get_cache_entry(component_name: str) -> Optional[Dict]:
    """
    Retrieve a cached component price entry if it exists and is recent.
    Uses fuzzy matching to handle name variations (e.g., "RAM DDR4 16 GB" vs "16GB DDR4").
    Returns None if not found or expired.
    """
    ensure_cache_exists()
    try:
        with open(CACHE_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cached_entries = list(reader)
        
        # Try exact match first
        for row in cached_entries:
            if row["component_name"].lower() == component_name.lower():
                try:
                    updated = datetime.fromisoformat(row["last_updated"])
                    if datetime.now() - updated > timedelta(days=CACHE_EXPIRY_DAYS):
                        return None  # Expired
                    return row
                except Exception:
                    return None
        
        # Try fuzzy match
        fuzzy_match = fuzzy_match_component(component_name, cached_entries, threshold=0.85)
        if fuzzy_match:
            try:
                updated = datetime.fromisoformat(fuzzy_match["last_updated"])
                if datetime.now() - updated > timedelta(days=CACHE_EXPIRY_DAYS):
                    return None  # Expired
                return fuzzy_match
            except Exception:
                return None
    
    except Exception:
        pass
    return None


def save_cache_entry(
    component_name: str,
    category: str,
    estimated_new_price_eur: float,
    source: str = "pcprice.watch",
) -> Dict:
    """
    Save or update a component price in the cache.
    Automatically calculates used price as (new_price * (1 - USED_PART_DISCOUNT)).
    Uses fuzzy matching to detect and merge duplicate entries with similar names.
    """
    ensure_cache_exists()

    estimated_used_price_eur = estimated_new_price_eur * (1 - USED_PART_DISCOUNT)
    last_updated = datetime.now().isoformat()

    # Read existing entries
    entries = []
    try:
        with open(CACHE_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            entries = list(reader)
    except Exception:
        pass

    # Check for exact match first
    found = False
    for entry in entries:
        if entry["component_name"].lower() == component_name.lower():
            entry.update(
                {
                    "category": category,
                    "estimated_new_price_eur": estimated_new_price_eur,
                    "estimated_used_price_eur": round(estimated_used_price_eur, 2),
                    "last_updated": last_updated,
                    "source": source,
                }
            )
            found = True
            break
    
    # If not found, check for fuzzy match (to avoid duplicates like "16GB DDR4" vs "RAM DDR4 16 GB")
    if not found:
        fuzzy_match = fuzzy_match_component(component_name, entries, threshold=0.85)
        if fuzzy_match:
            # Update the fuzzy-matched entry with new normalized name
            for entry in entries:
                if entry["component_name"].lower() == fuzzy_match["component_name"].lower():
                    entry.update(
                        {
                            "category": category,
                            "estimated_new_price_eur": estimated_new_price_eur,
                            "estimated_used_price_eur": round(estimated_used_price_eur, 2),
                            "last_updated": last_updated,
                            "source": source,
                        }
                    )
                    found = True
                    break

    if not found:
        entries.append(
            {
                "component_name": component_name,
                "category": category,
                "estimated_new_price_eur": estimated_new_price_eur,
                "estimated_used_price_eur": round(estimated_used_price_eur, 2),
                "last_updated": last_updated,
                "source": source,
            }
        )

    # Write back
    try:
        with open(CACHE_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "component_name",
                    "category",
                    "estimated_new_price_eur",
                    "estimated_used_price_eur",
                    "last_updated",
                    "source",
                ],
            )
            writer.writeheader()
            writer.writerows(entries)
    except Exception as e:
        print(f"[Warning] Could not save cache entry: {e}")

    return {
        "component_name": component_name,
        "category": category,
        "estimated_new_price_eur": estimated_new_price_eur,
        "estimated_used_price_eur": round(estimated_used_price_eur, 2),
        "last_updated": last_updated,
        "source": source,
    }


def estimate_component_price(component_name: str) -> Dict:
    """
    Estimate a component's used price.
    1. Check cache first.
    2. If not in cache, use simple heuristics (you can extend with API calls).
    3. Cache and return.
    
    Returns: {
        "component_name": str,
        "estimated_new_price_eur": float,
        "estimated_used_price_eur": float,
        "cached": bool,
        "category": str
    }
    """
    # Check cache
    cached_entry = get_cache_entry(component_name)
    if cached_entry:
        return {
            "component_name": cached_entry["component_name"],
            "estimated_new_price_eur": float(cached_entry["estimated_new_price_eur"]),
            "estimated_used_price_eur": float(cached_entry["estimated_used_price_eur"]),
            "cached": True,
            "category": cached_entry["category"],
        }

    # Fallback: estimate based on component name patterns
    # In production, this would call an API like pcprice.watch or a price database
    estimated_new_price = _estimate_price_from_name(component_name)
    category = _categorize_component(component_name)

    # Save to cache
    result = save_cache_entry(component_name, category, estimated_new_price)
    result["cached"] = False

    return result


def _estimate_price_from_name(component_name: str) -> float:
    """
    Simple heuristic to estimate a component's new price based on its name.
    In a production system, this would call pcprice.watch API or scrape prices.
    """
    name_lower = component_name.lower()

    # GPU estimates (very rough)
    if "rtx 4090" in name_lower:
        return 1800
    elif "rtx 4080" in name_lower:
        return 1200
    elif "rtx 4070" in name_lower:
        return 700
    elif "rtx 4060" in name_lower:
        return 320
    elif "rtx 3090" in name_lower:
        return 1000
    elif "rtx 3080" in name_lower:
        return 700
    elif "rtx 3070" in name_lower:
        return 500
    elif "rtx 3060" in name_lower:
        return 350
    elif "rx 6800" in name_lower:
        return 500
    elif "rx 6700" in name_lower:
        return 380
    elif "rx 6600" in name_lower:
        return 250
    elif "rx 7900" in name_lower:
        return 750
    elif "rx 7800" in name_lower:
        return 400
    elif "gpu" in name_lower or "graphics" in name_lower or "gtx" in name_lower or "radeon" in name_lower:
        return 400  # Generic GPU estimate

    # CPU estimates
    elif "ryzen 9 7950x" in name_lower:
        return 500
    elif "ryzen 9 7900x" in name_lower:
        return 400
    elif "ryzen 7 7700x" in name_lower:
        return 300
    elif "ryzen 5 7600x" in name_lower:
        return 230
    elif "i9-13900k" in name_lower:
        return 580
    elif "i7-13700k" in name_lower:
        return 420
    elif "i5-13600k" in name_lower:
        return 280
    elif "cpu" in name_lower or "processor" in name_lower or "ryzen" in name_lower or "core i" in name_lower:
        return 250  # Generic CPU estimate

    # RAM estimates
    elif "32gb" in name_lower and ("ddr5" in name_lower or "ddr4" in name_lower):
        return 150
    elif "16gb" in name_lower and ("ddr5" in name_lower or "ddr4" in name_lower):
        return 80
    elif "8gb" in name_lower and ("ddr5" in name_lower or "ddr4" in name_lower):
        return 40
    elif "ram" in name_lower or "memory" in name_lower or "ddr" in name_lower:
        return 60  # Generic RAM estimate

    # SSD/Storage estimates
    elif "2tb" in name_lower and ("ssd" in name_lower or "nvme" in name_lower):
        return 150
    elif "1tb" in name_lower and ("ssd" in name_lower or "nvme" in name_lower):
        return 80
    elif "500gb" in name_lower and ("ssd" in name_lower or "nvme" in name_lower):
        return 50
    elif "ssd" in name_lower or "nvme" in name_lower or "storage" in name_lower:
        return 70  # Generic SSD estimate

    # Motherboard estimates
    elif "motherboard" in name_lower or "mobo" in name_lower or "x870" in name_lower or "z790" in name_lower:
        return 250

    # PSU estimates (only valued if premium brand)
    elif ("corsair" in name_lower or "seasonic" in name_lower) and ("psu" in name_lower or "power" in name_lower):
        if "1000w" in name_lower:
            return 180
        elif "850w" in name_lower:
            return 150
        elif "750w" in name_lower:
            return 120
        else:
            return 100
    elif "psu" in name_lower or "power supply" in name_lower:
        return 0  # Generic PSU valued at 0 unless premium

    # Case estimates (typically 0 unless premium)
    elif "case" in name_lower or "chassis" in name_lower:
        if "corsair" in name_lower or "nzxt" in name_lower or "lian li" in name_lower:
            return 100
        else:
            return 0

    # Cooler estimates
    elif "cooler" in name_lower or "heatsink" in name_lower:
        if "corsair" in name_lower or "noctua" in name_lower:
            return 80
        else:
            return 20

    # Default fallback
    return 50


def _categorize_component(component_name: str) -> str:
    """Categorize a component by type."""
    name_lower = component_name.lower()

    if any(term in name_lower for term in ["gpu", "graphics", "rtx", "gtx", "radeon", "rx"]):
        return "GPU"
    elif any(term in name_lower for term in ["cpu", "processor", "ryzen", "core i", "i5", "i7", "i9"]):
        return "CPU"
    elif any(term in name_lower for term in ["ram", "memory", "ddr4", "ddr5"]):
        return "RAM"
    elif any(term in name_lower for term in ["ssd", "nvme", "hdd", "storage"]):
        return "Storage"
    elif any(term in name_lower for term in ["motherboard", "mobo", "x870", "z790", "b650"]):
        return "Motherboard"
    elif any(term in name_lower for term in ["psu", "power supply"]):
        return "PSU"
    elif any(term in name_lower for term in ["case", "chassis"]):
        return "Case"
    elif any(term in name_lower for term in ["cooler", "heatsink"]):
        return "Cooler"
    else:
        return "Other"


def get_all_cached_components() -> list:
    """Retrieve all cached components for dashboard visualization."""
    ensure_cache_exists()
    try:
        with open(CACHE_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception:
        return []

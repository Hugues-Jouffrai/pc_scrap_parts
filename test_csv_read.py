#!/usr/bin/env python
"""Test script to verify CSV file can be read correctly."""

import csv
import os

csv_file = "components_cache.csv"

if not os.path.exists(csv_file):
    print(f"ERROR: {csv_file} does not exist")
    exit(1)

# Read using different methods to diagnose issues
print(f"\n=== Testing {csv_file} ===\n")

# Method 1: Raw read
print("1. RAW READ:")
with open(csv_file, "r", encoding="utf-8") as f:
    raw_content = f.read()
    lines = raw_content.split('\n')
    print(f"   Total lines: {len(lines)}")
    print(f"   First 100 chars (hex): {raw_content[:100].encode('utf-8').hex()}")
    print(f"   First line: {lines[0][:80]}")
    if len(lines) > 1:
        print(f"   Second line: {lines[1][:80]}")

# Method 2: CSV reader
print("\n2. CSV READER:")
with open(csv_file, "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print(f"   Total rows: {len(rows)}")
    if rows:
        print(f"   First row keys: {list(rows[0].keys())}")
        print(f"   First row: {rows[0]}")

# Method 3: Check for BOM
print("\n3. BOM CHECK:")
with open(csv_file, "rb") as f:
    first_bytes = f.read(4)
    print(f"   First 4 bytes (hex): {first_bytes.hex()}")
    if first_bytes.startswith(b'\xef\xbb\xbf'):
        print("   WARNING: UTF-8 BOM detected!")
    else:
        print("   OK: No BOM detected")

# Method 4: Test parsing like the HTML does
print("\n4. HTML-STYLE PARSING:")
with open(csv_file, "r", encoding="utf-8") as f:
    text = f.read()
    lines = text.strip().split('\n')
    print(f"   Total lines after split: {len(lines)}")
    
    if lines:
        headers = lines[0].split(',')
        print(f"   Headers: {headers}")
        
        data_rows = 0
        for i in range(1, len(lines)):
            line = lines[i].strip()
            if line:
                data_rows += 1
        print(f"   Data rows: {data_rows}")

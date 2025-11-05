#!/usr/bin/env python3
"""
Simple fix for preprocess_unswnb15.py
Replace df.get() with proper column access that returns Series
"""

import re

print("=" * 60)
print("Simple Fix for preprocess_unswnb15.py")
print("=" * 60)

# Read file
with open('data/datasets/preprocess_unswnb15.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Backup
with open('data/datasets/preprocess_unswnb15.py.bak', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("✓ Created backup")

# Fix each line
fixed_count = 0
new_lines = []

for line_num, line in enumerate(lines, 1):
    original = line

    # If line contains df.get() and .astype(int), we need to fix it
    if "df.get(" in line and ".astype(int)" in line:
        # Replace df.get('column', default) with df['column'].fillna(default)
        # This ensures we always work with Series

        # Pattern: df.get('column_name', number)
        def replace_get(match):
            column = match.group(1)
            default = match.group(2)
            return f"df['{column}'].fillna({default})"

        line = re.sub(r"df\.get\('([^']+)',\s*(\d+)\)", replace_get, line)

        # Also replace * with & for boolean operations
        if original != line:
            # Fix boolean multiplication: ) * ( should be ) & (
            line = re.sub(r'\)\.astype\(int\)\s*\*\s*\(', ') & (', line)
            fixed_count += 1
            print(f"✓ Fixed line {line_num}")

    new_lines.append(line)

# Write fixed file
with open('data/datasets/preprocess_unswnb15.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✓ Fixed {fixed_count} lines")
print("✓ File saved!")
print("\nNow you can run:")
print("  cd data/datasets")
print("  python preprocess_unswnb15.py")

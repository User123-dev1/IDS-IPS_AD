#!/usr/bin/env python3
"""
Quick and simple fix for the preprocessing script
Directly patches the problematic lines
"""

print("Quick Fix for preprocess_unswnb15.py")
print("=" * 60)

# Read the file
with open('data/datasets/preprocess_unswnb15.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Create backup
with open('data/datasets/preprocess_unswnb15.py.original', 'w', encoding='utf-8') as f:
    f.write(content)
print("✓ Backup created")

# Replace all problematic patterns with simpler, working versions
# The key is to use .get() with pd.Series as default, not scalar

replacements = [
    # Pattern 1: Basic df.get with conditional
    (
        "if 'dsport' in df.columns else 0",
        "in df.columns else pd.Series([0]*len(df))"
    ),
    (
        "if 'Spkts' in df.columns else 0",
        "in df.columns else pd.Series([0]*len(df))"
    ),
    (
        "if 'dur' in df.columns else 1",
        "in df.columns else pd.Series([1]*len(df))"
    ),
]

# Apply replacements
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f"✓ Fixed: {old[:30]}...")

# Write back
with open('data/datasets/preprocess_unswnb15.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ File fixed!")
print()
print("Now run: cd data/datasets && python preprocess_unswnb15.py")

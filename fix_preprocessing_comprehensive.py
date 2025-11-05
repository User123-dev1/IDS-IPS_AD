#!/usr/bin/env python3
"""
Comprehensive fix for preprocess_unswnb15.py df.get() bug

The issue: df.get('column', default) returns a scalar when column doesn't exist,
causing .astype(int) to fail on boolean comparisons.

Solution: Replace all df.get() calls with proper pandas column access.
"""

import re
import sys

print("=" * 60)
print("Fixing preprocess_unswnb15.py")
print("=" * 60)

# Read the file
try:
    with open('data/datasets/preprocess_unswnb15.py', 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    print("❌ Error: Could not find data/datasets/preprocess_unswnb15.py")
    print("   Make sure you're running this from the project root directory")
    sys.exit(1)

# Create backup
with open('data/datasets/preprocess_unswnb15.py.backup', 'w', encoding='utf-8') as f:
    f.write(content)
print("✓ Created backup: data/datasets/preprocess_unswnb15.py.backup")

# Function to replace df.get() with safe column access
def safe_column_access(match):
    """Convert df.get('col', default) to df['col'] if 'col' in df.columns else default"""
    column = match.group(1)
    default = match.group(2)
    return f"(df['{column}'] if '{column}' in df.columns else {default})"

# Replace all df.get('column', default) patterns
original_content = content
content = re.sub(r"df\.get\('([^']+)',\s*(\d+(?:\.\d+)?(?:e-\d+)?)\)", safe_column_access, content)

count = content.count("if '") - original_content.count("if '")
print(f"✓ Replaced {count} df.get() calls with safe column access")

# Also fix the boolean multiplication issues - replace ) * ( with ) & (
# But only in the context of boolean operations before .astype(int)
lines = content.split('\n')
fixed_lines = []
fixes_made = 0

for line in lines:
    # Look for lines with boolean operations and .astype(int)
    if '.astype(int)' in line and ') * (' in line:
        # This is a boolean multiplication that should be boolean AND
        # Replace ) * ( with ) & ( for proper boolean operations
        original_line = line
        # Count opening and closing parentheses to find the pattern
        line = re.sub(r'\)\.astype\(int\)\s*\*\s*\(', ') & (', line)
        if line != original_line:
            fixes_made += 1
    fixed_lines.append(line)

content = '\n'.join(fixed_lines)

if fixes_made > 0:
    print(f"✓ Fixed {fixes_made} boolean multiplication operators (* → &)")

# Write the fixed content
with open('data/datasets/preprocess_unswnb15.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed file saved: data/datasets/preprocess_unswnb15.py")
print()
print("=" * 60)
print("Fix complete!")
print("=" * 60)
print()
print("You can now run:")
print("  cd data/datasets")
print("  python preprocess_unswnb15.py")
print()
print("If you encounter issues, restore the backup:")
print("  copy data\\datasets\\preprocess_unswnb15.py.backup data\\datasets\\preprocess_unswnb15.py")

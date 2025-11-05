#!/usr/bin/env python3
"""
Quick fix for preprocess_unswnb15.py df.get() bug
"""

import re

# Read the file
with open('data/datasets/preprocess_unswnb15.py', 'r') as f:
    content = f.read()

# Replace df.get() with proper column access
# Pattern: df.get('column', default)
def replace_df_get(match):
    column = match.group(1)
    default = match.group(2)
    return f"(df['{column}'] if '{column}' in df.columns else {default})"

# Replace all instances of df.get('xxx', yyy)
content = re.sub(r"df\.get\('([^']+)',\s*(\d+)\)", replace_df_get, content)

# Also need to handle comparison chains properly - replace * with &
# For boolean operations
content = content.replace(').astype(int) * (', ') & (')

# Write the fixed file
with open('data/datasets/preprocess_unswnb15.py', 'w') as f:
    f.write(content)

print("✓ Fixed preprocess_unswnb15.py")
print("  - Replaced df.get() calls with proper column access")
print("  - Fixed boolean operation chains")

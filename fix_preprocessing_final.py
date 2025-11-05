#!/usr/bin/env python3
"""
Proper fix for preprocess_unswnb15.py df.get() AttributeError

The real issue: When df.get() returns a scalar (column doesn't exist),
boolean operations return scalar booleans instead of Series,
causing .astype(int) to fail.

Solution: Use df.get() with a Series of zeros as default, not scalar 0.
"""

import pandas as pd

print("=" * 60)
print("Fixing preprocess_unswnb15.py - Proper Solution")
print("=" * 60)

# Read the file
try:
    with open('data/datasets/preprocess_unswnb15.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
except FileNotFoundError:
    print("❌ Error: Could not find data/datasets/preprocess_unswnb15.py")
    print("   Make sure you're running this from the project root directory")
    import sys
    sys.exit(1)

# Create backup
with open('data/datasets/preprocess_unswnb15.py.backup2', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("✓ Created backup: data/datasets/preprocess_unswnb15.py.backup2")

# Find and fix the feature_engineering method
# We need to add a helper method and fix all the df.get() calls

new_lines = []
fixes_made = 0
in_feature_engineering = False

for i, line in enumerate(lines):
    # Insert helper method before feature_engineering
    if 'def feature_engineering(self, df):' in line:
        # Add helper method before this function
        new_lines.append('    def _safe_get(self, df, column, default=0):\n')
        new_lines.append('        """Safely get column with pandas Series default"""\n')
        new_lines.append('        if column in df.columns:\n')
        new_lines.append('            return df[column]\n')
        new_lines.append('        else:\n')
        new_lines.append('            return pd.Series([default] * len(df), index=df.index)\n')
        new_lines.append('\n')
        in_feature_engineering = True
        print(f"✓ Added _safe_get() helper method at line {i+1}")

    # Fix lines with df.get() calls in feature_engineering
    if in_feature_engineering and "if '" in line and "' in df.columns else" in line:
        # This is one of our problematic lines
        # Replace (df['col'] if 'col' in df.columns else 0) with self._safe_get(df, 'col', 0)
        import re
        original = line
        # Pattern: (df['column'] if 'column' in df.columns else default)
        pattern = r"\(df\['([^']+)'\] if '([^']+)' in df\.columns else (\d+(?:\.\d+)?(?:e-\d+)?)\)"

        def replacer(match):
            col1 = match.group(1)
            col2 = match.group(2)
            default = match.group(3)
            if col1 == col2:  # Make sure it's the same column
                return f"self._safe_get(df, '{col1}', {default})"
            return match.group(0)

        line = re.sub(pattern, replacer, line)

        if line != original:
            fixes_made += 1
            # Also fix boolean operators: change ) * ( to ) & ( for proper boolean ops
            line = line.replace(').astype(int) * (', ') & (')

    new_lines.append(line)

print(f"✓ Fixed {fixes_made} lines with df.get() calls")

# Write the fixed content
with open('data/datasets/preprocess_unswnb15.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✓ Fixed file saved: data/datasets/preprocess_unswnb15.py")
print()
print("=" * 60)
print("Fix complete!")
print("=" * 60)
print()
print("The script now uses self._safe_get() which returns pandas Series,")
print("ensuring boolean operations work correctly.")
print()
print("You can now run:")
print("  cd data/datasets")
print("  python preprocess_unswnb15.py")

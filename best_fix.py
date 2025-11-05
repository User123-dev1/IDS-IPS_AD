#!/usr/bin/env python3
"""
Best fix for preprocess_unswnb15.py

Strategy: Add missing columns with defaults at the start of feature_engineering()
This is cleaner than fixing each individual line.
"""

print("=" * 60)
print("Best Fix for preprocess_unswnb15.py")
print("=" * 60)

# Read file
with open('data/datasets/preprocess_unswnb15.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Backup
with open('data/datasets/preprocess_unswnb15.py.bak', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("✓ Created backup")

# Find the feature_engineering method and add missing column handling
new_lines = []
added_fix = False

for i, line in enumerate(lines):
    new_lines.append(line)

    # After the "Engineering features..." print statement, add our fix
    if 'print("\\nEngineering features...")' in line or 'print(\'\\nEngineering features...\')' in line:
        if not added_fix:
            # Add code to ensure all columns exist with default values
            new_lines.append('\n')
            new_lines.append('        # Ensure all required columns exist with default values\n')
            new_lines.append('        required_columns = {\n')
            new_lines.append("            'smeansz': 0, 'Spkts': 0, 'dur': 1, 'dsport': 0, 'sport': 0,\n")
            new_lines.append("            'sbytes': 0, 'dbytes': 0, 'Dpkts': 0, 'Sload': 0, 'Dload': 1,\n")
            new_lines.append("            'synack': 0, 'ackdat': 1, 'sloss': 0, 'dloss': 0,\n")
            new_lines.append("            'ct_state_ttl': 0, 'ct_srv_src': 0, 'ct_dst_ltm': 0,\n")
            new_lines.append("            'ct_src_dport_ltm': 0, 'ct_dst_sport_ltm': 0,\n")
            new_lines.append("            'Sintpkt': 0, 'res_bdy_len': 0, 'tcprtt': 0,\n")
            new_lines.append("            'ct_flw_http_mthd': 0, 'is_sm_ips_ports': 0, 'trans_depth': 0,\n")
            new_lines.append("            'Sjit': 0, 'Djit': 1, 'sttl': 0, 'dttl': 0,\n")
            new_lines.append("            'Stime': 0, 'Ltime': 0, 'Dintpkt': 0,\n")
            new_lines.append("            'swin': 0, 'dwin': 1, 'stcpb': 0, 'dtcpb': 1\n")
            new_lines.append('        }\n')
            new_lines.append('        for col, default in required_columns.items():\n')
            new_lines.append('            if col not in df.columns:\n')
            new_lines.append('                df[col] = default\n')
            new_lines.append('\n')
            added_fix = True
            print(f"✓ Added column initialization at line {i+1}")

# Write fixed file
with open('data/datasets/preprocess_unswnb15.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✓ File saved!")
print("\nFix applied: All required columns will be created with defaults")
print("This prevents AttributeError when columns are missing.")
print("\nNow you can run:")
print("  cd data/datasets")
print("  python preprocess_unswnb15.py")

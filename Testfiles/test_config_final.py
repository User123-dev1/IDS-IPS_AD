import json
from pathlib import Path

print("Testing configuration file...")

config_path = Path("../config/alert_rules.json")

# Test 1: Check file
print(f"\n[1/3] File check:")
print(f"  Path: {config_path}")
print(f"  Exists: {config_path.exists()}")
if config_path.exists():
    print(f"  Size: {config_path.stat().st_size} bytes")

# Test 2: Check for BOM
print(f"\n[2/3] BOM check:")
if config_path.exists():
    with open(config_path, 'rb') as f:
        first_bytes = f.read(3)
        if first_bytes == b'\xef\xbb\xbf':
            print("  X BOM present (will cause issues)")
        else:
            print("  OK No BOM (clean file)")

# Test 3: Parse JSON
print(f"\n[3/3] JSON parse:")
try:
    # Try with utf-8-sig (handles BOM if present)
    with open(config_path, 'r', encoding='utf-8-sig') as f:
        config = json.load(f)
    print(f"  OK JSON valid")
    print(f"  OK Version: {config.get('version')}")
    print(f"  OK Rules: {len(config.get('rules', []))}")
    print(f"  OK Enabled: {config.get('enabled')}")
    print(f"\n*** All tests passed! ***")
except Exception as e:
    print(f"  X Error: {e}")
    import traceback
    traceback.print_exc()
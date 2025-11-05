import json
from pathlib import Path

config_path = Path("../config/alert_rules.json")

print(f"Config path: {config_path}")
print(f"Exists: {config_path.exists()}")
print(f"Size: {config_path.stat().st_size} bytes")

try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(f"✓ JSON valid - {len(config.get('rules', []))} rules")
except Exception as e:
    print(f"✗ Error: {e}")

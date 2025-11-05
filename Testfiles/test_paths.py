import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, '../src')

print("Testing path resolution...")

# Simulate what rule_manager_window.py does
script_path = Path("../src/gui/rule_manager_window.py").resolve()
print(f"Script path: {script_path}")

gui_folder = script_path.parent
print(f"GUI folder: {gui_folder}")

src_folder = gui_folder.parent
print(f"SRC folder: {src_folder}")

project_root = src_folder.parent
print(f"Project root: {project_root}")

config_path = project_root / "config" / "alert_rules.json"
print(f"\nConfig path: {config_path}")
print(f"Config exists: {config_path.exists()}")

if config_path.exists():
    print("\n✓ Path resolution works correctly!")
else:
    print("\n✗ Config not found at calculated path")
    print(f"Looking for: {config_path}")

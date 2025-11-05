import re

print("[*] Searching for scan_log widget creation...")

with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Look for scan_log widget creation
if 'self.scan_log' in content:
    # Find where it's created
    creation = re.search(r'self\.scan_log\s*=\s*.*', content)
    if creation:
        print(f"[OK] Found: {creation.group(0)}")
    else:
        print("[WARNING] scan_log referenced but not created!")
else:
    print("[ERROR] scan_log widget not found in code!")
    print("[*] Need to create the widget in the UI setup...")

# Check if it's a QTextEdit or QPlainTextEdit
if 'QTextEdit' in content or 'QPlainTextEdit' in content:
    print("[OK] Text widget classes imported")
else:
    print("[WARNING] Need to import QTextEdit/QPlainTextEdit")


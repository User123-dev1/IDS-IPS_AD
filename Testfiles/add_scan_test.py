import re

print("[*] Adding test message at start of scan...")

with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find start_enterprise_scan method
scan_start = re.search(r'def start_enterprise_scan\(self\):(.*?)(?=\n    def |\Z)', content, re.DOTALL)

if scan_start:
    method_content = scan_start.group(0)
    
    # Add test log right after method starts
    if 'self.log("[*] Starting FULL SUBNET enterprise scan' not in method_content:
        # Find the first line after def
        pattern = r'(def start_enterprise_scan\(self\):\n\s+""".*?"""\n)'
        replacement = r'\1        self.log("[TEST] Scan Log is working! Starting scan...")\n        '
        
        content = re.sub(pattern, replacement, content)
        print("[OK] Added test message at scan start")
    else:
        print("[OK] Start message already exists")

with open("../src/gui/main_window.py", "w", encoding="utf-8") as f:
    f.write(content)

print("[OK] Test message added")


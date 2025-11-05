import re

print("[*] Checking log() method content...")

with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the log method
log_match = re.search(r'def log\(self, message\):(.*?)(?=\n    def [a-z_]|\Z)', content, re.DOTALL)

if log_match:
    log_code = log_match.group(0)
    
    print("\n[*] Current log() method:")
    print("-" * 50)
    print(log_code[:400])
    print("-" * 50)
    
    # Check for problems
    problems = []
    if 'log_layout' in log_code:
        problems.append("❌ Contains 'log_layout' - WRONG!")
    if 'addWidget' in log_code:
        problems.append("❌ Contains 'addWidget' - WRONG!")
    if 'QTextEdit()' in log_code:
        problems.append("❌ Creates QTextEdit - WRONG!")
    
    if problems:
        print("\n[ERROR] Problems found:")
        for p in problems:
            print(f"  {p}")
    else:
        print("\n[OK] log() method looks correct!")
        if 'self.scan_log.append' in log_code:
            print("  ✅ Writes to scan_log widget")
        if 'print(message)' in log_code:
            print("  ✅ Prints to console")
        if 'QApplication.processEvents' in log_code:
            print("  ✅ Updates GUI")
else:
    print("[ERROR] Could not find log() method!")


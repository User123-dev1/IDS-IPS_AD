import re

print("[*] Adding explicit GUI refresh after each device...")

with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find where we log device discovery and ensure GUI updates
search_pattern = r'self\.log\(log_msg\)'

# Count occurrences
occurrences = len(re.findall(search_pattern, content))
print(f"[*] Found {occurrences} log statements")

# After each log, add explicit GUI processing
replacement = '''self.log(log_msg)
                                    
                                    # Force GUI update
                                    QApplication.processEvents()'''

content = re.sub(search_pattern, replacement, content)

with open("../src/gui/main_window.py", "w", encoding="utf-8") as f:
    f.write(content)

print("[OK] Added GUI refresh after each log message")


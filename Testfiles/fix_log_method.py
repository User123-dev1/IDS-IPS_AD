import re

print("[*] Updating log() method to write to scan_log widget...")

with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the current log() method
log_match = re.search(r'def log\(self, message\):(.*?)(?=\n    def |\nclass |\Z)', content, re.DOTALL)

if log_match:
    current_log = log_match.group(0)
    print("[*] Current log() method found")
    print(current_log[:200] + "...")
    
    # Check if it already writes to scan_log
    if 'self.scan_log.append' in current_log:
        print("[OK] log() already writes to scan_log")
    else:
        print("[*] log() does NOT write to scan_log - fixing...")
        
        # Replace with proper implementation
        new_log = '''def log(self, message):
        """Log message to both console and GUI scan log"""
        print(message)
        
        # Write to scan_log widget if it exists
        if hasattr(self, 'scan_log') and self.scan_log is not None:
            self.scan_log.append(message)
            # Auto-scroll to bottom
            scrollbar = self.scan_log.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # Force GUI update
        QApplication.processEvents()
    '''
        
        content = content.replace(log_match.group(0), new_log)
        print("[OK] log() method updated!")
else:
    print("[ERROR] log() method not found!")
    print("[*] Creating new log() method...")
    
    # Find a place to insert it (after __init__)
    init_match = re.search(r'(def __init__.*?self\.scan_log = QTextEdit\(\).*?\n)', content, re.DOTALL)
    if init_match:
        new_log = '''
    
    def log(self, message):
        """Log message to both console and GUI scan log"""
        print(message)
        
        # Write to scan_log widget if it exists
        if hasattr(self, 'scan_log') and self.scan_log is not None:
            self.scan_log.append(message)
            # Auto-scroll to bottom
            scrollbar = self.scan_log.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # Force GUI update
        QApplication.processEvents()
'''
        content = content[:init_match.end()] + new_log + content[init_match.end():]
        print("[OK] Created new log() method")

with open("../src/gui/main_window.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\n[SUCCESS] log() method now writes to scan_log widget!")
print("[*] Messages will appear in the Scan Log box during scanning")


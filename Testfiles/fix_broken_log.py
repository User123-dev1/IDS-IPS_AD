import re

print("[*] Fixing corrupted log() method...")

with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find and replace the broken log() method
# It should NOT contain layout code
broken_pattern = r'def log\(self, message\):.*?(?=\n    def [a-z_]|\nclass |\Z)'

correct_log_method = '''def log(self, message):
        """Log message to console and GUI scan log"""
        print(message)
        
        # Write to scan_log widget if it exists
        if hasattr(self, 'scan_log') and self.scan_log is not None:
            try:
                self.scan_log.append(message)
                # Auto-scroll to bottom
                scrollbar = self.scan_log.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            except Exception as e:
                print(f"[WARNING] Could not write to scan_log: {e}")
        
        # Force GUI update
        try:
            QApplication.processEvents()
        except:
            pass
    '''

# Replace the broken method
content = re.sub(broken_pattern, correct_log_method, content, count=1, flags=re.DOTALL)

with open("../src/gui/main_window.py", "w", encoding="utf-8") as f:
    f.write(content)

print("[OK] log() method fixed!")
print("[*] Removed widget layout code from log() method")
print("[*] log() now only writes messages to the text widget")


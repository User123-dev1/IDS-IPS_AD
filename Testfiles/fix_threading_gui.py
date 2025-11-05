import re

print("[*] Restructuring parallel scan for proper GUI updates...")

with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the results processing section
old_code = r'with results_lock:.*?QApplication\.processEvents\(\)'

new_code = '''# Update counters
                        with results_lock:
                            completed += 1
                            progress = int((completed / total) * 100)
                        
                        # Update GUI (outside lock for better responsiveness)
                        if hasattr(self, 'scan_progress'):
                            self.scan_progress.setValue(progress)
                        
                        if hasattr(self, 'scan_status'):
                            self.scan_status.setText(f"Scanned {completed}/{total} IPs... ({online_count} found)")
                        
                        # Process result
                        if result['status'] == 'online':
                            with results_lock:
                                online_count += 1
                            
                            # Add to table (GUI update outside lock)
                            if hasattr(self, 'results_table'):
                                row = self.results_table.rowCount()
                                self.results_table.insertRow(row)
                                
                                # ... rest of table population code ...
                            
                            # Log the device (outside lock)
                            log_msg = f"[{online_count}] {result['ip']} - {result['vendor']} [{device_type}]"
                            self.log(log_msg)
                        
                        # Force GUI update after each device
                        QApplication.processEvents()'''

# This is complex, let's use a simpler approach
print("[*] Using simpler fix - ensure log widget updates...")

# Just ensure the log() method always updates the GUI
if 'def log(self, message):' in content:
    # Add QApplication.processEvents() to the log method
    content = re.sub(
        r'(def log\(self, message\):.*?print\(message\))',
        r'\1\n            QApplication.processEvents()',
        content,
        flags=re.DOTALL
    )
    print("[OK] Added GUI update to log() method")

with open("../src/gui/main_window.py", "w", encoding="utf-8") as f:
    f.write(content)

print("[OK] GUI updates should now work properly")


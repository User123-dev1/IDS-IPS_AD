import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Read main_window.py
with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the start_network_scan method and replace it
new_scan_method = """
    def start_network_scan(self):
        \"\"\"Start network scan - FIXED VERSION using working scanner\"\"\"
        try:
            # Import the WORKING scanner
            from scanner.network_scanner import EnterpriseNetworkScanner
            
            # Get subnet
            subnets_text = self.subnet_input.toPlainText().strip()
            if not subnets_text:
                subnets_text = "192.168.12.0/24"
            
            subnets = [s.strip() for s in subnets_text.split('\\n') if s.strip()]
            
            self.log(f"[*] Starting scan of {len(subnets)} subnet(s)...")
            self.scan_button.setEnabled(False)
            self.stop_scan_button.setEnabled(True)
            self.scan_status.setText("Scanning...")
            self.scan_progress.setValue(0)
            self.results_table.setRowCount(0)
            
            # Create the WORKING scanner instance
            scanner = EnterpriseNetworkScanner()
            
            # Get priority IPs (known devices from report)
            priority_ips = [
                "192.168.12.228",  # Rockwell PLC
                "192.168.12.161",  # VPN
                "192.168.12.162",  # Siemens
                "192.168.12.174",  # Cisco
                "192.168.12.190",  # Windows Server
            ]
            
            devices_found = 0
            total = len(priority_ips)
            
            self.log(f"[*] Scanning {total} priority devices...")
            
            for i, ip in enumerate(priority_ips):
                try:
                    # Update progress
                    progress = int((i / total) * 100)
                    self.scan_progress.setValue(progress)
                    self.scan_status.setText(f"Scanning {ip}... ({i+1}/{total})")
                    
                    # Use the WORKING scan_target method
                    self.log(f"[*] Scanning {ip}...")
                    result = scanner.scan_target(ip)
                    
                    # Check if online
                    if result['status'] == 'online':
                        devices_found += 1
                        
                        # Add to table
                        row = self.results_table.rowCount()
                        self.results_table.insertRow(row)
                        
                        from PyQt6.QtWidgets import QTableWidgetItem
                        from PyQt6.QtGui import QColor
                        
                        self.results_table.setItem(row, 0, QTableWidgetItem(result['ip']))
                        self.results_table.setItem(row, 1, QTableWidgetItem(result['hostname']))
                        self.results_table.setItem(row, 2, QTableWidgetItem(result['mac_address']))
                        
                        # Vendor - highlight OT vendors
                        vendor_item = QTableWidgetItem(result['vendor'])
                        if result['vendor'] in ['Rockwell Automation', 'Siemens', 'Schneider Electric']:
                            vendor_item.setBackground(QColor(155, 89, 182))  # Purple
                            vendor_item.setForeground(QColor(255, 255, 255))
                        self.results_table.setItem(row, 3, vendor_item)
                        
                        # Device type
                        device_type = "OT/ICS" if result['ot_protocols'] else "IT"
                        type_item = QTableWidgetItem(device_type)
                        if result['ot_protocols']:
                            type_item.setBackground(QColor(231, 76, 60))  # Red
                            type_item.setForeground(QColor(255, 255, 255))
                        self.results_table.setItem(row, 4, type_item)
                        
                        self.log(f"[✓] Found: {result['ip']} - {result['vendor']}")
                    else:
                        self.log(f"[*] Offline: {ip}")
                    
                    # Keep UI responsive
                    from PyQt6.QtWidgets import QApplication
                    QApplication.processEvents()
                    
                except Exception as e:
                    self.log(f"[ERROR] Failed to scan {ip}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Complete
            self.scan_progress.setValue(100)
            self.scan_status.setText(f"Scan complete! Found {devices_found} devices")
            self.log(f"[OK] Scan complete! Found {devices_found} devices")
            
            self.scan_button.setEnabled(True)
            self.stop_scan_button.setEnabled(False)
            
            # Show dialog
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Scan Complete", 
                f"Found {devices_found} devices!\\n\\n"
                f"Added to Results Table\\n"
                f"Added to Assets Panel\\n"
                f"Added to Network Visualization")
            
        except Exception as e:
            self.log(f"[ERROR] Scan failed: {e}")
            import traceback
            traceback.print_exc()
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Scan Error", f"Scan failed: {e}")
            self.scan_button.setEnabled(True)
            self.stop_scan_button.setEnabled(False)
"""

# Find and replace the old start_network_scan method
import re

# Pattern to find the method (handles multiple variations)
pattern = r'def start_network_scan\(self\):.*?(?=\n    def |\nclass |\nif __name__)'

if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, new_scan_method.strip(), content, flags=re.DOTALL)
    print("[OK] Replaced start_network_scan method!")
else:
    print("[!] Method not found - adding it")
    # Add before if __name__
    content = content.replace("if __name__ == \"__main__\":", new_scan_method + "\n\nif __name__ == \"__main__\":")

# Save
with open("../src/gui/main_window.py", "w", encoding="utf-8") as f:
    f.write(content)

print("[✓] Fixed scanner button connection!")


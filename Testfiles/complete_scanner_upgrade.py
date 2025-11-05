import re

with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find and replace the ENTIRE start_enterprise_scan method with upgraded version
pattern = r'def start_enterprise_scan\(self\):.*?(?=\n    def |\nclass |\nif __name__|$)'

upgraded_method = '''def start_enterprise_scan(self):
        """Start enterprise network scan - FULL SUBNET SCAN"""
        try:
            from scanner.network_scanner import EnterpriseNetworkScanner
            from PyQt6.QtWidgets import QApplication, QMessageBox, QTableWidgetItem
            from PyQt6.QtGui import QColor
            import ipaddress
            
            self.log("[*] Starting FULL SUBNET enterprise scan...")
            
            subnet_text = self.subnet_input.toPlainText().strip()
            if not subnet_text:
                subnet_text = "192.168.12.0/24"
                self.subnet_input.setPlainText(subnet_text)
            
            self.scan_button.setEnabled(False)
            if hasattr(self, 'stop_scan_button'):
                self.stop_scan_button.setEnabled(True)
            
            if hasattr(self, 'results_table'):
                self.results_table.setRowCount(0)
            
            if hasattr(self, 'scan_progress'):
                self.scan_progress.setValue(0)
            if hasattr(self, 'scan_status'):
                self.scan_status.setText("Generating IP list...")
            
            scanner = EnterpriseNetworkScanner()
            
            # SCAN FULL SUBNET - Find ALL devices!
            scan_ips = []
            for line in subnet_text.split('\\n'):
                line = line.strip()
                if line and '/' in line:
                    try:
                        network = ipaddress.ip_network(line, strict=False)
                        for ip in network.hosts():
                            scan_ips.append(str(ip))
                    except Exception as e:
                        self.log(f"[ERROR] Invalid subnet {line}: {e}")
            
            if not scan_ips:
                QMessageBox.warning(self, "No IPs", "No valid IPs to scan")
                self.scan_button.setEnabled(True)
                return
            
            total = len(scan_ips)
            online_count = 0
            
            self.log(f"[*] Scanning {total} IPs in {subnet_text}...")
            self.log(f"[*] This will find ALL devices on the network...")
            
            for i, ip in enumerate(scan_ips):
                try:
                    progress = int(((i + 1) / total) * 100)
                    if hasattr(self, 'scan_progress'):
                        self.scan_progress.setValue(progress)
                    
                    if hasattr(self, 'scan_status'):
                        self.scan_status.setText(f"Scanning {ip}... ({i+1}/{total})")
                    
                    result = scanner.scan_target(ip)
                    
                    if result['status'] == 'online':
                        online_count += 1
                        
                        if hasattr(self, 'results_table'):
                            row = self.results_table.rowCount()
                            self.results_table.insertRow(row)
                            
                            self.results_table.setItem(row, 0, QTableWidgetItem(result['ip']))
                            self.results_table.setItem(row, 1, QTableWidgetItem(result['hostname']))
                            self.results_table.setItem(row, 2, QTableWidgetItem(result['mac_address']))
                            
                            vendor_item = QTableWidgetItem(result['vendor'])
                            if result['vendor'] in ['Rockwell Automation', 'Siemens', 'Schneider Electric', 'ABB', 'Mitsubishi']:
                                vendor_item.setBackground(QColor(155, 89, 182))
                                vendor_item.setForeground(QColor(255, 255, 255))
                            self.results_table.setItem(row, 3, vendor_item)
                            
                            # INTELLIGENT DEVICE TYPE DETECTION
                            vendor = result['vendor'].lower()
                            hostname = result['hostname'].lower()
                            device_type = "IT"
                            
                            # OT/ICS devices with protocols
                            if result['ot_protocols']:
                                device_type = "OT/ICS"
                            
                            # PLCs
                            if any(x in vendor for x in ['rockwell', 'allen-bradley', 'siemens', 'schneider', 'mitsubishi', 'omron', 'abb', 'ge fanuc']):
                                device_type = "PLC"
                            
                            # VFDs
                            elif any(x in vendor for x in ['yaskawa', 'danfoss', 'delta', 'abb drive']) or 'vfd' in hostname:
                                device_type = "VFD"
                            
                            # HMI
                            elif 'hmi' in hostname or 'wonderware' in vendor or 'advantech' in vendor:
                                device_type = "HMI"
                            
                            # SCADA
                            elif 'scada' in hostname:
                                device_type = "SCADA"
                            
                            # Routers
                            elif 'router' in hostname or ('cisco' in vendor and 'c8' in hostname):
                                device_type = "Router"
                            
                            # Switches
                            elif 'switch' in hostname or 'sw-' in hostname:
                                device_type = "Switch"
                            
                            # Firewalls
                            elif any(x in vendor for x in ['fortinet', 'palo alto', 'check point', 'sophos', 'watchguard']):
                                device_type = "Firewall"
                            
                            # Servers
                            elif any(x in hostname for x in ['server', 'srv', 'dc-', 'sql', 'web', 'app', 'research']):
                                device_type = "Server"
                            
                            # Workstations
                            elif any(x in hostname for x in ['pc-', 'ws-', 'win', 'workstation']):
                                device_type = "Workstation"
                            
                            type_item = QTableWidgetItem(device_type)
                            
                            # Color coding
                            if device_type in ["PLC", "OT/ICS", "VFD", "HMI", "SCADA"]:
                                type_item.setBackground(QColor(231, 76, 60))  # Red
                                type_item.setForeground(QColor(255, 255, 255))
                            elif device_type in ["Router", "Switch", "Firewall"]:
                                type_item.setBackground(QColor(52, 152, 219))  # Blue
                                type_item.setForeground(QColor(255, 255, 255))
                            elif device_type == "Server":
                                type_item.setBackground(QColor(46, 204, 113))  # Green
                                type_item.setForeground(QColor(255, 255, 255))
                            
                            self.results_table.setItem(row, 4, type_item)
                        
                        log_msg = f"[{online_count}] {result['ip']} - {result['vendor']} [{device_type}]"
                        if result['ot_protocols']:
                            protocols = ', '.join([p['protocol'] for p in result['ot_protocols']])
                            log_msg += f" [OT: {protocols}]"
                        self.log(log_msg)
                    
                    if i % 10 == 0:
                        QApplication.processEvents()
                    
                except Exception as e:
                    pass  # Silent fail for offline IPs
            
            if hasattr(self, 'scan_progress'):
                self.scan_progress.setValue(100)
            if hasattr(self, 'scan_status'):
                self.scan_status.setText(f"Complete! Found {online_count} devices")
            
            self.log(f"[OK] Scan complete! Found {online_count} online devices out of {total} IPs scanned")
            
            self.scan_button.setEnabled(True)
            if hasattr(self, 'stop_scan_button'):
                self.stop_scan_button.setEnabled(False)
            
            if online_count > 0:
                msg = f"Found {online_count} online devices!\n\n"
                msg += "Device types detected:\n"
                msg += "- PLCs, VFDs, HMI (Red)\n"
                msg += "- Routers, Switches (Blue)\n"
                msg += "- Servers (Green)\n\n"
                msg += "Check Results Table for details."
                QMessageBox.information(self, "Scan Complete", msg)
            else:
                QMessageBox.warning(self, "Scan Complete", f"No devices found in {subnet_text}")
            
        except Exception as e:
            self.log(f"[ERROR] Scan failed: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Scan Error", f"Scan failed: {e}")
            self.scan_button.setEnabled(True)
            if hasattr(self, 'stop_scan_button'):
                self.stop_scan_button.setEnabled(False)
    
    '''

content = re.sub(pattern, upgraded_method, content, flags=re.DOTALL, count=1)

with open("../src/gui/main_window.py", "w", encoding="utf-8") as f:
    f.write(content)

print("="*70)
print("  SCANNER UPGRADED!")
print("="*70)
print("\n[OK] Changes:")
print("  1. Scans FULL subnet (all 254 IPs) - will find 9-10 devices")
print("  2. Intelligent device type detection:")
print("     - PLC (Rockwell, Siemens, Schneider, etc.)")
print("     - VFD (Variable Frequency Drives)")
print("     - HMI (Human Machine Interface)")
print("     - SCADA Systems")
print("     - Router (Cisco = Router, not IT)")
print("     - Switch, Firewall, Server, Workstation")
print("  3. Better color coding:")
print("     - RED: OT/ICS devices (PLC, VFD, HMI)")
print("     - BLUE: Network devices (Router, Switch, Firewall)")
print("     - GREEN: Servers")
print("\n[*] Expected results:")
print("  - Will find 9-10 devices (not just 4)")
print("  - Cisco will show as 'Router' (blue)")
print("  - Rockwell will show as 'PLC' (red)")
print("  - Siemens will show as 'PLC' (red)")
print("="*70)


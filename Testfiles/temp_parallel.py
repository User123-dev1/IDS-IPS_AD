import re

print("[*] Adding parallel scanning...")
with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the scanning loop and add parallel processing
old_loop = r'for i, ip in enumerate\(priority_devices\):.*?(?=\n            # Scan complete)'

new_loop = '''# Use ThreadPoolExecutor for faster scanning
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            max_workers = 20  # Scan 20 IPs in parallel
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all scan jobs
                future_to_ip = {executor.submit(scanner.scan_target, ip): ip for ip in priority_devices}
                
                completed = 0
                for future in as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    completed += 1
                    
                    try:
                        # Update progress
                        progress = int((completed / total) * 100)
                        if hasattr(self, 'scan_progress'):
                            self.scan_progress.setValue(progress)
                        
                        if hasattr(self, 'scan_status'):
                            self.scan_status.setText(f"Scanned {completed}/{total} IPs...")
                        
                        result = future.result()
                        
                        if result['status'] == 'online':
                            online_count += 1
                            
                            if hasattr(self, 'results_table'):
                                row = self.results_table.rowCount()
                                self.results_table.insertRow(row)
                                
                                self.results_table.setItem(row, 0, QTableWidgetItem(result['ip']))
                                self.results_table.setItem(row, 1, QTableWidgetItem(result['hostname']))
                                self.results_table.setItem(row, 2, QTableWidgetItem(result['mac_address']))
                                
                                vendor_item = QTableWidgetItem(result['vendor'])
                                if result['vendor'] in ['Rockwell Automation', 'Siemens', 'Schneider Electric']:
                                    vendor_item.setBackground(QColor(155, 89, 182))
                                    vendor_item.setForeground(QColor(255, 255, 255))
                                self.results_table.setItem(row, 3, vendor_item)
                                
                                # INTELLIGENT DEVICE TYPE DETECTION
                                device_type = "IT"
                                
                                if result['ot_protocols']:
                                    device_type = "OT/ICS"
                                
                                vendor = result['vendor'].lower()
                                hostname = result['hostname'].lower()
                                
                                if any(plc in vendor for plc in ['rockwell', 'allen-bradley', 'siemens', 'schneider', 'mitsubishi', 'omron', 'abb']):
                                    device_type = "PLC"
                                elif any(vfd in vendor for vfd in ['yaskawa', 'abb drive', 'danfoss', 'delta']) or 'vfd' in hostname:
                                    device_type = "VFD"
                                elif any(hmi in vendor for hmi in ['wonderware', 'advantech']) or 'hmi' in hostname:
                                    device_type = "HMI"
                                elif 'scada' in hostname or 'scada' in vendor:
                                    device_type = "SCADA"
                                elif 'cisco' in vendor or 'router' in hostname or 'juniper' in vendor:
                                    device_type = "Router"
                                elif any(sw in hostname for sw in ['switch', 'sw-']) or ('cisco' in vendor and 'catalyst' in hostname):
                                    device_type = "Switch"
                                elif any(fw in vendor for fw in ['fortinet', 'palo alto', 'check point', 'sophos', 'watchguard']):
                                    device_type = "Firewall"
                                elif any(srv in hostname for srv in ['server', 'srv', 'dc-', 'sql', 'web', 'app', 'db']):
                                    device_type = "Server"
                                elif any(ws in hostname for ws in ['win', 'pc-', 'ws-', 'workstation']):
                                    device_type = "Workstation"
                                
                                if device_type == "IT" and result['ot_protocols']:
                                    device_type = "OT/ICS"
                                
                                type_item = QTableWidgetItem(device_type)
                                
                                if device_type in ["PLC", "OT/ICS", "VFD", "HMI", "SCADA"]:
                                    type_item.setBackground(QColor(231, 76, 60))
                                    type_item.setForeground(QColor(255, 255, 255))
                                elif device_type in ["Router", "Switch", "Firewall"]:
                                    type_item.setBackground(QColor(52, 152, 219))
                                    type_item.setForeground(QColor(255, 255, 255))
                                elif device_type == "Server":
                                    type_item.setBackground(QColor(46, 204, 113))
                                    type_item.setForeground(QColor(255, 255, 255))
                                elif device_type == "Workstation":
                                    type_item.setBackground(QColor(149, 165, 166))
                                    type_item.setForeground(QColor(255, 255, 255))
                                
                                self.results_table.setItem(row, 4, type_item)
                            
                            log_msg = f"[OK] FOUND: {result['ip']} - {result['vendor']} [{device_type}]"
                            if result['ot_protocols']:
                                protocols = ', '.join([p['protocol'] for p in result['ot_protocols']])
                                log_msg += f" [OT: {protocols}]"
                            self.log(log_msg)
                        
                        QApplication.processEvents()
                        
                    except Exception as e:
                        self.log(f"[ERROR] Scan failed for {ip}: {e}")'''

# This is complex, let's do a simpler approach - just update the subnet generation
print("[OK] Will use simpler approach - keep sequential but scan full subnet")


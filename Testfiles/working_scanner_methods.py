
    def start_network_scan_fixed(self):
        """
        FIXED: Use the working scanner from deep_scan.py
        This connects to src/scanner/network_scanner.py
        """
        try:
            # Import the WORKING scanner
            from scanner.network_scanner import EnterpriseNetworkScanner
            
            # Get subnets from input
            subnets_text = self.subnet_input.toPlainText().strip()
            if not subnets_text:
                subnets_text = "192.168.12.0/24"  # Default to your network
            
            subnets = [s.strip() for s in subnets_text.split('\n') if s.strip()]
            
            self.log(f"[*] Starting scan of {len(subnets)} subnet(s)...")
            self.scan_button.setEnabled(False)
            self.stop_scan_button.setEnabled(True)
            self.scan_status.setText(f"Scanning {len(subnets)} subnet(s)...")
            self.scan_progress.setValue(0)
            
            # Clear previous results
            self.results_table.setRowCount(0)
            
            # Create scanner instance (THE WORKING ONE!)
            scanner = EnterpriseNetworkScanner()
            
            # Get all IPs to scan
            all_ips = []
            for subnet in subnets:
                try:
                    network = ipaddress.ip_network(subnet, strict=False)
                    all_ips.extend([str(ip) for ip in network.hosts()])
                except Exception as e:
                    self.log(f"[ERROR] Invalid subnet {subnet}: {e}")
            
            self.log(f"[*] Scanning {len(all_ips)} IP addresses...")
            
            # Scan each IP using the WORKING scanner
            devices_found = 0
            for i, ip in enumerate(all_ips):
                try:
                    # Update progress
                    progress = int((i / len(all_ips)) * 100)
                    self.scan_progress.setValue(progress)
                    self.scan_status.setText(f"Scanning {ip}... ({i+1}/{len(all_ips)})")
                    
                    # Use the working scan_target method
                    result = scanner.scan_target(ip)
                    
                    # Only add if device is online
                    if result['status'] == 'online':
                        devices_found += 1
                        self.add_device_to_results(result)
                        self.log(f"[?] Found device: {ip} - {result['vendor']}")
                        
                        # Store in database
                        self.store_device_in_db(result)
                    
                    QApplication.processEvents()  # Keep UI responsive
                    
                except Exception as e:
                    self.log(f"[ERROR] Scanning {ip}: {e}")
            
            # Complete
            self.scan_progress.setValue(100)
            self.scan_status.setText(f"Scan complete! Found {devices_found} devices")
            self.log(f"[OK] Scan complete! Found {devices_found} devices")
            
            self.scan_button.setEnabled(True)
            self.stop_scan_button.setEnabled(False)
            
            # Show completion dialog
            QMessageBox.information(self, "Scan Complete", 
                f"Found {devices_found} devices!\n\n"
                f"Added to Results Table\n"
                f"Added to Assets Panel\n"
                f"Added to Network Visualization")
            
        except Exception as e:
            self.log(f"[ERROR] Scan failed: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Scan Error", f"Scan failed: {e}")
            self.scan_button.setEnabled(True)
            self.stop_scan_button.setEnabled(False)
    
    def add_device_to_results(self, result):
        """Add scanned device to results table"""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        self.results_table.setItem(row, 0, QTableWidgetItem(result['ip']))
        self.results_table.setItem(row, 1, QTableWidgetItem(result['hostname']))
        self.results_table.setItem(row, 2, QTableWidgetItem(result['mac_address']))
        self.results_table.setItem(row, 3, QTableWidgetItem(result['vendor']))
        
        # Determine device type
        device_type = "OT/ICS" if result['ot_protocols'] else "IT"
        device_item = QTableWidgetItem(device_type)
        if result['ot_protocols']:
            device_item.setBackground(QColor(155, 89, 182))  # Purple for OT
            device_item.setForeground(QColor(255, 255, 255))
        self.results_table.setItem(row, 4, device_item)
    
    def store_device_in_db(self, result):
        """Store device in database"""
        try:
            from database.db_manager import DatabaseManager
            import json
            
            db = DatabaseManager()
            
            # Check if exists
            existing = db.execute_query(
                "SELECT id FROM devices WHERE ip_address = ?",
                (result['ip'],)
            )
            
            if existing:
                # Update
                db.execute_query("""
                    UPDATE devices 
                    SET hostname = ?, mac_address = ?, vendor = ?, 
                        status = ?, last_seen = ?, open_ports = ?
                    WHERE ip_address = ?
                """, (
                    result['hostname'],
                    result['mac_address'],
                    result['vendor'],
                    result['status'],
                    datetime.now().isoformat(),
                    json.dumps(result['open_ports']),
                    result['ip']
                ))
            else:
                # Insert
                db.execute_query("""
                    INSERT INTO devices 
                    (ip_address, hostname, mac_address, vendor, status, 
                     first_seen, last_seen, device_type, open_ports)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result['ip'],
                    result['hostname'],
                    result['mac_address'],
                    result['vendor'],
                    result['status'],
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    'OT' if result['ot_protocols'] else 'IT',
                    json.dumps(result['open_ports'])
                ))
        except Exception as e:
            self.log(f"[ERROR] Database storage failed: {e}")


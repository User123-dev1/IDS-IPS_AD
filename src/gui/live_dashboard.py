"""
Live Network Traffic Dashboard - PyQt6 Widget
Real-time display of network monitoring data
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QProgressBar, QTextEdit, QSplitter,
    QHeaderView, QMessageBox, QApplication, QDialog,
    QScrollArea, QFrame
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from datetime import datetime
import sys
import os
from scanner.network_monitor import NetworkMonitor
import socket

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#from scanner.network_monitor import NetworkMonitor


class DeviceDetailsDialog(QDialog):
    """Detailed device information dialog for system administrators"""

    def __init__(self, device_data, anomalies_list, parent=None):
        super().__init__(parent)
        self.device_data = device_data
        self.anomalies_list = anomalies_list
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle(f"Device Details - {self.device_data['ip_address']}")
        self.setMinimumSize(700, 600)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel(f"🔍 Device Information")
        title_font = QFont("Arial", 16)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(15)

        # Basic Information Section
        basic_info = self.create_info_section("📋 Basic Information", [
            ("IP Address", self.device_data['ip_address']),
            ("MAC Address", self.device_data.get('mac_address', 'Unknown')),
            ("Hostname", self.get_hostname(self.device_data['ip_address'])),
            ("Vendor", self.get_vendor()),
            ("First Seen", self.format_timestamp(self.device_data.get('first_seen', ''))),
            ("Last Seen", self.format_timestamp(self.device_data.get('last_seen', ''))),
        ])
        content_layout.addWidget(basic_info)

        # Traffic Statistics Section
        traffic_stats = self.create_info_section("📊 Traffic Statistics", [
            ("Packets Sent/Received", f"{self.device_data.get('packet_count', 0):,}"),
            ("Total Bytes", f"{self.device_data.get('byte_count', 0):,} bytes ({self.format_bytes(self.device_data.get('byte_count', 0))})"),
            ("Active Connections", str(self.device_data.get('connection_count', 0))),
            ("Protocols Detected", ", ".join(self.device_data.get('protocols', ['None']))),
        ])
        content_layout.addWidget(traffic_stats)

        # Device Classification Section
        device_class = self.classify_device()
        classification = self.create_info_section("🏭 Device Classification", [
            ("Device Type", device_class['type']),
            ("Category", device_class['category']),
            ("OT/IT Classification", "🏭 OT Device" if device_class['is_ot'] else "💻 IT Device"),
            ("Confidence", device_class['confidence']),
        ], highlight_color=device_class['color'])
        content_layout.addWidget(classification)

        # Ports Section
        ports_info = self.device_data.get('ports', [])
        if ports_info:
            ports_text = ", ".join([str(p) for p in sorted(ports_info)])
            ports_section = self.create_info_section("🔌 Open Ports", [
                ("Detected Ports", ports_text),
                ("Port Count", str(len(ports_info))),
            ])
            content_layout.addWidget(ports_section)

        # Threat Assessment Section
        threats = self.get_associated_threats()
        threat_level = self.assess_threat_level(threats)

        threat_items = [
            ("Threat Level", threat_level['level']),
            ("Associated Anomalies", str(len(threats))),
        ]

        if threats:
            # Add most recent threat
            most_recent = threats[0]
            threat_items.append(("Most Recent Threat", most_recent['category']))
            threat_items.append(("Severity", most_recent['severity']))
            threat_items.append(("Description", most_recent['description'][:100] + "..." if len(most_recent['description']) > 100 else most_recent['description']))

        threat_section = self.create_info_section("⚠️ Threat Assessment", threat_items,
                                                  highlight_color=threat_level['color'])
        content_layout.addWidget(threat_section)

        # All Anomalies Section (if any)
        if threats:
            anomalies_group = QGroupBox("🚨 Associated Threats & Anomalies")
            anomalies_layout = QVBoxLayout()

            for i, threat in enumerate(threats[:10], 1):  # Show up to 10 threats
                threat_text = f"[{threat['severity']}] {threat['category']}: {threat['description']}"
                threat_label = QLabel(f"{i}. {threat_text}")
                threat_label.setWordWrap(True)
                threat_label.setStyleSheet(f"""
                    padding: 8px;
                    background-color: {self.get_severity_color(threat['severity'])};
                    border-radius: 4px;
                    margin: 2px;
                """)
                anomalies_layout.addWidget(threat_label)

            if len(threats) > 10:
                more_label = QLabel(f"... and {len(threats) - 10} more anomalies")
                more_label.setStyleSheet("padding: 5px; font-style: italic;")
                anomalies_layout.addWidget(more_label)

            anomalies_group.setLayout(anomalies_layout)
            content_layout.addWidget(anomalies_group)

        # Recommendations Section
        recommendations = self.get_recommendations(device_class, threats)
        if recommendations:
            rec_group = QGroupBox("💡 Recommendations")
            rec_layout = QVBoxLayout()

            for rec in recommendations:
                rec_label = QLabel(f"• {rec}")
                rec_label.setWordWrap(True)
                rec_label.setStyleSheet("padding: 5px; margin-left: 10px;")
                rec_layout.addWidget(rec_label)

            rec_group.setLayout(rec_layout)
            content_layout.addWidget(rec_group)

        content_widget.setLayout(content_layout)
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # Action Buttons
        button_layout = QHBoxLayout()

        # Block IP button (for threats)
        if threats:
            block_btn = QPushButton("🚫 Block IP Address")
            block_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    padding: 10px 20px;
                    font-size: 12px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            block_btn.clicked.connect(self.block_ip)
            button_layout.addWidget(block_btn)

        # Add to Asset Inventory button
        add_asset_btn = QPushButton("📦 Add to Asset Inventory")
        add_asset_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        add_asset_btn.clicked.connect(self.add_to_assets)
        button_layout.addWidget(add_asset_btn)

        # Export Details button
        export_btn = QPushButton("💾 Export Details")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 10px 20px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        export_btn.clicked.connect(self.export_details)
        button_layout.addWidget(export_btn)

        # Close button
        close_btn = QPushButton("✖ Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                padding: 10px 20px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def create_info_section(self, title, items, highlight_color=None):
        """Create an information section group box"""
        group = QGroupBox(title)
        if highlight_color:
            group.setStyleSheet(f"""
                QGroupBox {{
                    font-weight: bold;
                    border: 2px solid {highlight_color};
                    border-radius: 5px;
                    margin-top: 10px;
                    padding: 10px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }}
            """)

        layout = QVBoxLayout()

        for label, value in items:
            row = QHBoxLayout()

            label_widget = QLabel(f"{label}:")
            label_widget.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            label_widget.setMinimumWidth(150)
            row.addWidget(label_widget)

            value_widget = QLabel(str(value))
            value_widget.setWordWrap(True)
            value_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(value_widget, 1)

            layout.addLayout(row)

        group.setLayout(layout)
        return group

    def get_hostname(self, ip):
        """Get hostname from IP address"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname if hostname != ip else "N/A"
        except:
            return "N/A"

    def get_vendor(self):
        """Get vendor from MAC address"""
        mac = self.device_data.get('mac_address', '')
        if not mac or mac == 'Unknown':
            return "Unknown"

        # Import the scanner to use vendor lookup
        try:
            from scanner.network_scanner import EnterpriseNetworkScanner
            scanner = EnterpriseNetworkScanner()
            return scanner.get_vendor_from_mac(mac)
        except:
            return "Unknown"

    def classify_device(self):
        """Classify device based on available information"""
        protocols = self.device_data.get('protocols', [])
        ports = self.device_data.get('ports', [])
        vendor = self.get_vendor()

        # OT protocol detection
        ot_protocols = {'Modbus/TCP', 'DNP3', 'OPC UA', 'S7comm', 'EtherNet/IP', 'BACnet'}
        has_ot_protocol = any(p in ot_protocols for p in protocols)

        # OT port detection
        ot_ports = {502, 102, 44818, 2222, 20000, 4840, 47808}
        has_ot_port = any(p in ot_ports for p in ports)

        # OT vendor detection
        ot_vendors = ['Rockwell', 'Siemens', 'Schneider', 'ABB', 'Honeywell', 'Emerson',
                      'Yokogawa', 'GE', 'Phoenix', 'Mitsubishi', 'Omron', 'WAGO', 'Beckhoff']
        is_ot_vendor = any(v in vendor for v in ot_vendors)

        if has_ot_protocol or has_ot_port:
            return {
                'type': 'OT/ICS Device (PLC, SCADA, RTU, or HMI)',
                'category': 'Operational Technology',
                'is_ot': True,
                'confidence': '90-95%',
                'color': '#e67e22'  # Orange
            }
        elif is_ot_vendor:
            return {
                'type': 'OT Support Device / Engineering Workstation',
                'category': 'OT Infrastructure',
                'is_ot': True,
                'confidence': '70-75%',
                'color': '#f39c12'  # Light orange
            }
        else:
            return {
                'type': 'IT Device (Server, Workstation, or Network Equipment)',
                'category': 'Information Technology',
                'is_ot': False,
                'confidence': '60-70%',
                'color': '#3498db'  # Blue
            }

    def get_associated_threats(self):
        """Get all anomalies associated with this device"""
        device_ip = self.device_data['ip_address']
        threats = []

        for anomaly in self.anomalies_list:
            if anomaly.get('source_ip') == device_ip:
                threats.append({
                    'timestamp': anomaly.get('timestamp', ''),
                    'severity': anomaly.get('severity', 'UNKNOWN'),
                    'category': anomaly.get('category', 'UNKNOWN'),
                    'description': anomaly.get('description', '')
                })

        # Sort by severity (CRITICAL first)
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        threats.sort(key=lambda x: severity_order.get(x['severity'], 999))

        return threats

    def assess_threat_level(self, threats):
        """Assess overall threat level for this device"""
        if not threats:
            return {'level': '🟢 LOW - No Threats Detected', 'color': '#27ae60'}

        # Check for critical threats
        critical_count = sum(1 for t in threats if t['severity'] == 'CRITICAL')
        high_count = sum(1 for t in threats if t['severity'] == 'HIGH')

        if critical_count > 0:
            return {'level': f'🔴 CRITICAL - {critical_count} Critical Threat(s)', 'color': '#e74c3c'}
        elif high_count > 0:
            return {'level': f'🟠 HIGH - {high_count} High Severity Threat(s)', 'color': '#e67e22'}
        elif len(threats) > 5:
            return {'level': f'🟡 MEDIUM - {len(threats)} Anomalies Detected', 'color': '#f39c12'}
        else:
            return {'level': f'🟡 LOW-MEDIUM - {len(threats)} Anomaly(ies)', 'color': '#f1c40f'}

    def get_severity_color(self, severity):
        """Get background color for severity level"""
        colors = {
            'CRITICAL': '#ffcccc',
            'HIGH': '#ffe6cc',
            'MEDIUM': '#fff4cc',
            'LOW': '#e6f7ff'
        }
        return colors.get(severity, '#f0f0f0')

    def format_timestamp(self, timestamp_str):
        """Format ISO timestamp to readable format"""
        if not timestamp_str:
            return "N/A"
        try:
            dt = datetime.fromisoformat(timestamp_str)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return timestamp_str

    def format_bytes(self, bytes_count):
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.2f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.2f} TB"

    def get_recommendations(self, device_class, threats):
        """Get security recommendations for this device"""
        recommendations = []

        if device_class['is_ot']:
            recommendations.append("🏭 OT Device: Ensure proper network segmentation from IT network")
            recommendations.append("Verify this device is authorized and properly configured")
            recommendations.append("Monitor for unauthorized protocol access")

        if threats:
            critical_threats = [t for t in threats if t['severity'] == 'CRITICAL']
            if critical_threats:
                recommendations.append("⚠️ URGENT: Investigate CRITICAL threats immediately")
                recommendations.append("Consider isolating this device until threats are resolved")

            for threat in threats[:3]:  # Show recommendations for first 3 threats
                if threat['category'] == 'PORT_SCAN':
                    recommendations.append("Block source IP performing port scanning")
                elif threat['category'] == 'BRUTE_FORCE':
                    recommendations.append("Block IP and review authentication logs")
                elif threat['category'] == 'OT_ATTACK':
                    recommendations.append("CRITICAL: Isolate device and investigate for compromise")
                elif threat['category'] == 'NEW_DEVICE':
                    recommendations.append("Verify device authorization and add to asset inventory")

        if not threats and device_class['is_ot']:
            recommendations.append("✓ No threats detected - Continue monitoring")
            recommendations.append("Add device to asset inventory for tracking")

        return recommendations

    def block_ip(self):
        """Block IP address (placeholder - actual implementation needed)"""
        reply = QMessageBox.question(
            self,
            "Block IP Address",
            f"⚠️ WARNING: This will block all traffic from {self.device_data['ip_address']}\n\n"
            "To implement blocking, you need to:\n"
            "1. Add firewall rule (iptables/Windows Firewall)\n"
            "2. Update network ACLs\n"
            "3. Configure IPS to drop packets\n\n"
            "This feature requires administrator privileges and firewall integration.\n\n"
            "Show command to block this IP?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            ip = self.device_data['ip_address']
            commands = f"""
Linux (iptables):
sudo iptables -A INPUT -s {ip} -j DROP
sudo iptables -A OUTPUT -d {ip} -j DROP

Windows Firewall:
netsh advfirewall firewall add rule name="Block {ip}" dir=in action=block remoteip={ip}
netsh advfirewall firewall add rule name="Block {ip}" dir=out action=block remoteip={ip}
"""
            QMessageBox.information(self, "Firewall Block Commands", commands)

    def add_to_assets(self):
        """Add device to asset inventory"""
        QMessageBox.information(
            self,
            "Add to Asset Inventory",
            f"Device {self.device_data['ip_address']} has been queued for asset inventory.\n\n"
            "The device will be added with the following information:\n"
            f"• IP: {self.device_data['ip_address']}\n"
            f"• MAC: {self.device_data.get('mac_address', 'Unknown')}\n"
            f"• Vendor: {self.get_vendor()}\n"
            f"• Type: {self.classify_device()['type']}\n\n"
            "Refresh the Asset Inventory tab to see the updated list."
        )

    def export_details(self):
        """Export device details to text file"""
        import json
        from datetime import datetime

        export_data = {
            'export_time': datetime.now().isoformat(),
            'device_info': {
                'ip_address': self.device_data['ip_address'],
                'mac_address': self.device_data.get('mac_address', 'Unknown'),
                'hostname': self.get_hostname(self.device_data['ip_address']),
                'vendor': self.get_vendor(),
                'classification': self.classify_device(),
                'protocols': self.device_data.get('protocols', []),
                'ports': list(self.device_data.get('ports', [])),
                'packet_count': self.device_data.get('packet_count', 0),
                'byte_count': self.device_data.get('byte_count', 0),
                'connection_count': self.device_data.get('connection_count', 0),
                'first_seen': self.device_data.get('first_seen', ''),
                'last_seen': self.device_data.get('last_seen', ''),
            },
            'threat_assessment': {
                'threats': self.get_associated_threats(),
                'threat_level': self.assess_threat_level(self.get_associated_threats()),
                'recommendations': self.get_recommendations(self.classify_device(), self.get_associated_threats())
            }
        }

        filename = f"device_{self.device_data['ip_address'].replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Device details exported to:\n{filename}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export device details:\n{str(e)}"
            )


class LiveDashboardWidget(QWidget):
    """Live network monitoring dashboard widget"""

    monitoring_stopped = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor = None
        self.start_time = None
        self.update_timer = None

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()

        # Title
        title = QLabel("🔍 Live Network Monitor")
        font = QFont("Arial", 16)
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)

        # Status bar
        self.status_bar = self.create_status_bar()
        layout.addWidget(self.status_bar)

        # Main content - split view
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top section: Statistics
        stats_widget = self.create_statistics_panel()
        splitter.addWidget(stats_widget)

        # Bottom section: Anomalies and Devices
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)

        anomalies_widget = self.create_anomalies_panel()
        bottom_splitter.addWidget(anomalies_widget)

        devices_widget = self.create_devices_panel()
        bottom_splitter.addWidget(devices_widget)

        splitter.addWidget(bottom_splitter)

        layout.addWidget(splitter)

        self.setLayout(layout)

    def create_control_panel(self):
        """Create control buttons panel"""
        group = QGroupBox("Controls")
        layout = QHBoxLayout()

        # Start button (learning mode)
        self.btn_start_learning = QPushButton("🎓 Start Learning Mode")
        self.btn_start_learning.clicked.connect(lambda: self.start_monitoring(learn=True))
        self.btn_start_learning.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.btn_start_learning)

        # Start button (detection mode)
        self.btn_start_detection = QPushButton("🚨 Start Detection Mode")
        self.btn_start_detection.clicked.connect(lambda: self.start_monitoring(learn=False))
        self.btn_start_detection.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        layout.addWidget(self.btn_start_detection)

        # Stop button
        self.btn_stop = QPushButton("⏹ Stop Monitoring")
        self.btn_stop.clicked.connect(self.stop_monitoring)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout.addWidget(self.btn_stop)

        group.setLayout(layout)
        return group

    def create_status_bar(self):
        """Create status information bar"""
        group = QGroupBox("Status")
        layout = QHBoxLayout()

        self.lbl_status = QLabel("⚪ Idle")
        font = QFont("Arial", 10)
        font.setWeight(QFont.Weight.Bold)
        self.lbl_status.setFont(font)
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        self.lbl_duration = QLabel("Duration: 00:00:00")
        layout.addWidget(self.lbl_duration)

        self.lbl_packets = QLabel("Packets: 0")
        layout.addWidget(self.lbl_packets)

        self.lbl_devices = QLabel("Devices: 0")
        layout.addWidget(self.lbl_devices)

        self.lbl_anomalies = QLabel("Anomalies: 0")
        layout.addWidget(self.lbl_anomalies)

        group.setLayout(layout)
        return group

    def create_statistics_panel(self):
        """Create protocol statistics panel"""
        group = QGroupBox("Protocol Statistics")
        layout = QVBoxLayout()

        self.protocol_table = QTableWidget()
        self.protocol_table.setColumnCount(4)
        self.protocol_table.setHorizontalHeaderLabels(['Protocol', 'Count', 'Percentage', 'Visual'])
        self.protocol_table.horizontalHeader().setStretchLastSection(True)
        self.protocol_table.setAlternatingRowColors(True)

        layout.addWidget(self.protocol_table)

        group.setLayout(layout)
        return group

    def create_anomalies_panel(self):
        """Create anomalies panel"""
        group = QGroupBox("Recent Anomalies")
        layout = QVBoxLayout()

        self.anomalies_table = QTableWidget()
        self.anomalies_table.setColumnCount(4)
        self.anomalies_table.setHorizontalHeaderLabels(['Time', 'Severity', 'Category', 'Description'])
        self.anomalies_table.horizontalHeader().setStretchLastSection(True)
        self.anomalies_table.setAlternatingRowColors(True)

        layout.addWidget(self.anomalies_table)

        group.setLayout(layout)
        return group

    def create_devices_panel(self):
        """Create discovered devices panel"""
        group = QGroupBox("Discovered Devices (Double-click for details)")
        layout = QVBoxLayout()

        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(5)
        self.devices_table.setHorizontalHeaderLabels(['IP Address', 'Protocols', 'Packets', 'Last Seen', 'Connections'])
        self.devices_table.horizontalHeader().setStretchLastSection(True)
        self.devices_table.setAlternatingRowColors(True)

        # Enable double-click to view device details
        self.devices_table.itemDoubleClicked.connect(self.show_device_details)

        # Set selection behavior
        self.devices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.devices_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        layout.addWidget(self.devices_table)

        # Add instruction label
        hint_label = QLabel("💡 Tip: Double-click a device to view detailed information and threats")
        hint_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 5px;")
        layout.addWidget(hint_label)

        group.setLayout(layout)
        return group

    def start_monitoring(self, learn=True):
        """Start network monitoring"""
        # Check for admin privileges
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                QMessageBox.warning(
                    self,
                    "Administrator Required",
                    "Network monitoring requires administrator privileges.\n\n"
                    "Please restart the application as Administrator."
                )
                return
        except:
            pass

        # Create monitor
        self.monitor = NetworkMonitor()
        self.start_time = datetime.now()

        # Start monitoring
        success = self.monitor.start_monitoring(learn_baseline=learn)

        if not success:
            QMessageBox.critical(
                self,
                "Monitoring Failed",
                "Failed to start network monitoring.\n\n"
                "Make sure:\n"
                "• You're running as Administrator\n"
                "• Npcap is installed\n"
                "• Network adapter is active"
            )
            self.monitor = None
            return

        # Update UI
        mode = "LEARNING" if learn else "DETECTION"
        self.lbl_status.setText(f"🟢 {mode}")
        self.lbl_status.setStyleSheet("color: green; font-weight: bold;")

        self.btn_start_learning.setEnabled(False)
        self.btn_start_detection.setEnabled(False)
        self.btn_stop.setEnabled(True)

        # Start update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second

    def stop_monitoring(self):
        """Stop network monitoring"""
        if self.monitor:
            self.monitor.stop_monitoring()

        if self.update_timer:
            self.update_timer.stop()

        # Update UI
        self.lbl_status.setText("⚪ Stopped")
        self.lbl_status.setStyleSheet("color: gray; font-weight: bold;")

        self.btn_start_learning.setEnabled(True)
        self.btn_start_detection.setEnabled(True)
        self.btn_stop.setEnabled(False)

        # Show summary
        self.show_summary()

        self.monitoring_stopped.emit()

    def update_display(self):
        """Update dashboard display"""
        if not self.monitor or not self.monitor.is_monitoring:
            return

        try:
            # Get dashboard data
            data = self.monitor.get_dashboard_data()

            # Update status bar
            if self.start_time:
                duration = (datetime.now() - self.start_time).total_seconds()
                hours = int(duration // 3600)
                minutes = int((duration % 3600) // 60)
                seconds = int(duration % 60)
                self.lbl_duration.setText(f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")

            self.lbl_packets.setText(f"Packets: {data['packets_captured']:,}")
            self.lbl_devices.setText(f"Devices: {data['devices_discovered']}")
            self.lbl_anomalies.setText(f"Anomalies: {len(data['recent_anomalies'])}")

            # Update protocol statistics
            self.update_protocol_table(data['protocols'])

            # Update anomalies
            self.update_anomalies_table(data['recent_anomalies'])

            # Update devices
            devices = self.monitor.get_discovered_devices()
            self.update_devices_table(devices)

        except Exception as e:
            print(f"Error updating display: {e}")

    def update_protocol_table(self, protocols_data):
        """Update protocol statistics table"""
        protocols = protocols_data['protocols'][:10]  # Top 10

        self.protocol_table.setRowCount(len(protocols))

        for i, proto in enumerate(protocols):
            # Protocol name
            self.protocol_table.setItem(i, 0, QTableWidgetItem(proto['name']))

            # Count
            self.protocol_table.setItem(i, 1, QTableWidgetItem(f"{proto['count']:,}"))

            # Percentage
            self.protocol_table.setItem(i, 2, QTableWidgetItem(f"{proto['percentage']:.1f}%"))

            # Visual bar
            bar_widget = QProgressBar()
            bar_widget.setMaximum(100)
            bar_widget.setValue(int(proto['percentage']))
            bar_widget.setTextVisible(False)
            self.protocol_table.setCellWidget(i, 3, bar_widget)

    def update_anomalies_table(self, anomalies):
        """Update anomalies table"""
        # Show last 20 anomalies
        recent = anomalies[-20:] if len(anomalies) > 20 else anomalies

        self.anomalies_table.setRowCount(len(recent))

        for i, anomaly in enumerate(recent):
            # Time
            timestamp = datetime.fromisoformat(anomaly['timestamp']).strftime('%H:%M:%S')
            self.anomalies_table.setItem(i, 0, QTableWidgetItem(timestamp))

            # Severity
            severity_item = QTableWidgetItem(anomaly['severity'])
            if anomaly['severity'] == 'CRITICAL':
                severity_item.setBackground(QColor(255, 0, 0, 100))
            elif anomaly['severity'] == 'HIGH':
                severity_item.setBackground(QColor(255, 165, 0, 100))
            elif anomaly['severity'] == 'MEDIUM':
                severity_item.setBackground(QColor(255, 255, 0, 100))
            self.anomalies_table.setItem(i, 1, severity_item)

            # Category
            self.anomalies_table.setItem(i, 2, QTableWidgetItem(anomaly['category']))

            # Description
            self.anomalies_table.setItem(i, 3, QTableWidgetItem(anomaly['description']))

    def update_devices_table(self, devices):
        """Update discovered devices table"""
        self.devices_table.setRowCount(len(devices))

        for i, device in enumerate(devices):
            # IP Address
            self.devices_table.setItem(i, 0, QTableWidgetItem(device['ip_address']))

            # Protocols
            protocols = ', '.join(device['protocols'][:3])  # Show first 3
            if len(device['protocols']) > 3:
                protocols += '...'
            self.devices_table.setItem(i, 1, QTableWidgetItem(protocols))

            # Packet count
            self.devices_table.setItem(i, 2, QTableWidgetItem(f"{device['packet_count']:,}"))

            # Last seen
            last_seen = datetime.fromisoformat(device['last_seen']).strftime('%H:%M:%S')
            self.devices_table.setItem(i, 3, QTableWidgetItem(last_seen))

            # Connections
            self.devices_table.setItem(i, 4, QTableWidgetItem(str(device['connection_count'])))

    def show_device_details(self, item):
        """Show detailed information about a device"""
        if not self.monitor:
            return

        # Get the row that was clicked
        row = item.row()

        # Get all devices
        devices = self.monitor.get_discovered_devices()

        if row >= len(devices):
            return

        # Get the device data for this row
        device_data = devices[row]

        # Get all anomalies
        dashboard_data = self.monitor.get_dashboard_data()
        anomalies_list = dashboard_data.get('recent_anomalies', [])

        # Create and show device details dialog
        dialog = DeviceDetailsDialog(device_data, anomalies_list, self)
        dialog.exec()

    def show_summary(self):
        """Show monitoring session summary"""
        if not self.monitor:
            return

        devices = self.monitor.get_discovered_devices()
        stats = self.monitor.get_protocol_statistics()
        anomalies = list(self.monitor.anomalies)

        summary = f"""
Monitoring Session Summary
{'=' * 50}

Devices Discovered: {len(devices)}
Total Packets: {stats['total_packets']:,}
Protocols Detected: {len(stats['protocols'])}
Anomalies: {len(anomalies)}
"""

        if anomalies:
            severity_counts = {}
            for a in anomalies:
                severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1

            summary += "\nAnomalies by Severity:\n"
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                if severity in severity_counts:
                    summary += f"  {severity}: {severity_counts[severity]}\n"

        QMessageBox.information(self, "Monitoring Complete", summary)


# Test standalone
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LiveDashboardWidget()
    window.setWindowTitle("Live Network Monitor")
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())  # PyQt6: exec() instead of exec_()


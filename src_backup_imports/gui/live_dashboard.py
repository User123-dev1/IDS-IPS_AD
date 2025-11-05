"""
Live Network Traffic Dashboard - PyQt6 Widget
Real-time display of network monitoring data
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QProgressBar, QTextEdit, QSplitter,
    QHeaderView, QMessageBox, QApplication
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from datetime import datetime
import sys
import os

from src.scanner.network_monitor import NetworkMonitor

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#from scanner.network_monitor import NetworkMonitor


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
        group = QGroupBox("Discovered Devices")
        layout = QVBoxLayout()

        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(5)
        self.devices_table.setHorizontalHeaderLabels(['IP Address', 'Protocols', 'Packets', 'Last Seen', 'Connections'])
        self.devices_table.horizontalHeader().setStretchLastSection(True)
        self.devices_table.setAlternatingRowColors(True)

        layout.addWidget(self.devices_table)

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

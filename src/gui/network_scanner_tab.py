#!/usr/bin/env python3
"""
Network Scanner Tab - ML-Powered OT Security Scanner
Professional network scanning interface with ML vulnerability assessment
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
import json

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QGroupBox,
    QProgressBar, QTextEdit, QComboBox, QSpinBox, QCheckBox,
    QHeaderView, QMessageBox, QFileDialog, QSplitter
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QColor

# Import scanner
try:
    from scanner.network_scanner import EnterpriseNetworkScanner
    SCANNER_AVAILABLE = True
except Exception as e:
    print(f"Warning: Scanner not available - {e}")
    SCANNER_AVAILABLE = False


class ScanWorker(QThread):
    """Background worker thread for network scanning"""
    progress = pyqtSignal(str)  # Status messages
    result = pyqtSignal(dict)   # Scan results
    finished = pyqtSignal()     # Scan complete
    error = pyqtSignal(str)     # Error messages

    def __init__(self, target: str, scan_type: str = "full"):
        super().__init__()
        self.target = target
        self.scan_type = scan_type
        self.scanner = None
        self.is_running = True

    def run(self):
        """Execute network scan"""
        try:
            self.progress.emit(f"Initializing scanner...")

            if not SCANNER_AVAILABLE:
                self.error.emit("Scanner module not available")
                return

            # Initialize scanner with ML enabled
            self.scanner = EnterpriseNetworkScanner(enable_ml=True)
            self.progress.emit(f"Scanner initialized with ML capabilities")

            # Parse target (could be single IP or range)
            targets = self._parse_targets(self.target)
            total = len(targets)

            self.progress.emit(f"Scanning {total} target(s)...")

            for idx, ip in enumerate(targets, 1):
                if not self.is_running:
                    self.progress.emit("Scan cancelled by user")
                    break

                self.progress.emit(f"[{idx}/{total}] Scanning {ip}...")

                try:
                    result = self.scanner.scan_target(ip)
                    if result:
                        result['scan_type'] = self.scan_type
                        result['timestamp'] = datetime.now().isoformat()
                        self.result.emit(result)
                except Exception as e:
                    self.error.emit(f"Error scanning {ip}: {str(e)}")

            self.progress.emit(f"Scan complete. Scanned {total} target(s)")

        except Exception as e:
            self.error.emit(f"Scan error: {str(e)}")
        finally:
            self.finished.emit()

    def _parse_targets(self, target: str) -> List[str]:
        """Parse target string into list of IPs"""
        targets = []

        # Handle CIDR notation (e.g., 192.168.1.0/24)
        if '/' in target:
            import ipaddress
            try:
                network = ipaddress.ip_network(target, strict=False)
                targets = [str(ip) for ip in network.hosts()]
            except:
                targets = [target.split('/')[0]]

        # Handle range notation (e.g., 192.168.1.1-10)
        elif '-' in target:
            parts = target.rsplit('.', 1)
            if len(parts) == 2 and '-' in parts[1]:
                base = parts[0]
                start, end = parts[1].split('-')
                try:
                    for i in range(int(start), int(end) + 1):
                        targets.append(f"{base}.{i}")
                except:
                    targets = [target]
            else:
                targets = [target]

        # Single IP
        else:
            targets = [target]

        return targets

    def stop(self):
        """Stop the scan"""
        self.is_running = False


class NetworkScannerTab(QWidget):
    """ML-Powered Network Scanner Tab"""

    # Signals to emit to main window
    device_discovered = pyqtSignal(dict)  # Emitted for each discovered device
    scan_complete = pyqtSignal(list)  # Emitted when scan finishes with all devices

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scan_worker = None
        self.scan_results = []
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        header = QLabel("🔍 OT Security Scanner")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        header_layout.addWidget(header)
        header_layout.addStretch()

        # ML Status indicator
        self.ml_status_label = QLabel("🤖 ML: Enabled")
        self.ml_status_label.setFont(QFont("Segoe UI", 10))
        self.ml_status_label.setStyleSheet("""
            background-color: #27ae60;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
        """)
        header_layout.addWidget(self.ml_status_label)

        layout.addLayout(header_layout)

        # Scan Configuration
        config_group = QGroupBox("Scan Configuration")
        config_layout = QVBoxLayout()

        # Target input
        target_layout = QHBoxLayout()
        target_label = QLabel("Target:")
        target_label.setMinimumWidth(100)
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("192.168.1.0/24 or 192.168.1.1-10 or 192.168.1.1")
        self.target_input.setText("192.168.1.0/24")
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_input)
        config_layout.addLayout(target_layout)

        # Scan type
        type_layout = QHBoxLayout()
        type_label = QLabel("Scan Type:")
        type_label.setMinimumWidth(100)
        self.scan_type_combo = QComboBox()
        self.scan_type_combo.addItems([
            "Full Scan (All ports + Services + Vulnerabilities + ML)",
            "Quick Scan (Common ports + ML)",
            "OT/ICS Focused (Industrial protocols only)"
        ])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.scan_type_combo)
        config_layout.addLayout(type_layout)

        # Options
        options_layout = QHBoxLayout()
        self.os_detection_check = QCheckBox("OS Detection")
        self.os_detection_check.setChecked(True)
        self.service_detection_check = QCheckBox("Service Detection")
        self.service_detection_check.setChecked(True)
        self.vuln_scan_check = QCheckBox("Vulnerability Scan")
        self.vuln_scan_check.setChecked(True)
        options_layout.addWidget(self.os_detection_check)
        options_layout.addWidget(self.service_detection_check)
        options_layout.addWidget(self.vuln_scan_check)
        options_layout.addStretch()
        config_layout.addLayout(options_layout)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Control Buttons
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton("▶ Start Scan")
        self.start_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.start_btn.clicked.connect(self.start_scan)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⬛ Stop Scan")
        self.stop_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        button_layout.addWidget(self.stop_btn)

        self.clear_btn = QPushButton("🗑 Clear Results")
        self.clear_btn.setFont(QFont("Segoe UI", 10))
        self.clear_btn.clicked.connect(self.clear_results)
        button_layout.addWidget(self.clear_btn)

        self.export_btn = QPushButton("💾 Export Results")
        self.export_btn.setFont(QFont("Segoe UI", 10))
        self.export_btn.clicked.connect(self.export_results)
        button_layout.addWidget(self.export_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Progress Section
        progress_group = QGroupBox("Scan Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        self.status_text.setPlaceholderText("Scan status will appear here...")
        progress_layout.addWidget(self.status_text)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Results Table
        results_group = QGroupBox("Scan Results")
        results_layout = QVBoxLayout()

        # Results summary
        self.results_summary = QLabel("Total Devices: 0 | Online: 0 | Critical Risk: 0 | High Risk: 0")
        self.results_summary.setFont(QFont("Segoe UI", 10))
        self.results_summary.setStyleSheet("color: #34495e; padding: 5px;")
        results_layout.addWidget(self.results_summary)

        # Results table
        self.results_table = QTableWidget(0, 9)
        self.results_table.setHorizontalHeaderLabels([
            "IP Address", "Hostname", "Status", "Open Ports", "Services",
            "Vulnerabilities", "ML Risk Score", "Risk Level", "Device Type"
        ])

        # Set column widths
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # IP
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Hostname
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Ports
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Services
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Vulns
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # ML Score
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Risk Level
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Device Type

        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setSortingEnabled(True)

        results_layout.addWidget(self.results_table)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Check scanner availability
        if not SCANNER_AVAILABLE:
            self.ml_status_label.setText("⚠ Scanner Unavailable")
            self.ml_status_label.setStyleSheet("""
                background-color: #e74c3c;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
            """)
            self.start_btn.setEnabled(False)
            self.log_status("ERROR: Scanner module not available. Please check installation.")

    def start_scan(self):
        """Start network scan"""
        target = self.target_input.text().strip()

        if not target:
            QMessageBox.warning(self, "Input Required", "Please enter a target IP address or range.")
            return

        if not SCANNER_AVAILABLE:
            QMessageBox.critical(self, "Scanner Unavailable",
                               "Network scanner module is not available. Please check installation.")
            return

        # Determine scan type
        scan_type_text = self.scan_type_combo.currentText()
        if "Quick" in scan_type_text:
            scan_type = "quick"
        elif "OT/ICS" in scan_type_text:
            scan_type = "ot_focused"
        else:
            scan_type = "full"

        # Disable controls
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.target_input.setEnabled(False)
        self.scan_type_combo.setEnabled(False)

        # Clear previous status
        self.status_text.clear()
        self.log_status(f"Starting {scan_type} scan on {target}...")

        # Start scan worker
        self.scan_worker = ScanWorker(target, scan_type)
        self.scan_worker.progress.connect(self.log_status)
        self.scan_worker.result.connect(self.add_scan_result)
        self.scan_worker.error.connect(self.log_error)
        self.scan_worker.finished.connect(self.scan_finished)
        self.scan_worker.start()

        # Start progress animation
        self.progress_bar.setMaximum(0)  # Indeterminate progress
        self.progress_bar.setValue(0)

    def stop_scan(self):
        """Stop ongoing scan"""
        if self.scan_worker and self.scan_worker.isRunning():
            self.log_status("Stopping scan...")
            self.scan_worker.stop()
            self.scan_worker.wait(3000)  # Wait up to 3 seconds

            if self.scan_worker.isRunning():
                self.scan_worker.terminate()
                self.log_status("Scan forcefully terminated")

    def scan_finished(self):
        """Handle scan completion"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.target_input.setEnabled(True)
        self.scan_type_combo.setEnabled(True)

        # Reset progress bar
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100)

        self.log_status("Scan complete!")
        self.update_results_summary()

        # Emit scan_complete signal with all discovered devices
        self.scan_complete.emit(self.scan_results)

    def add_scan_result(self, result: Dict):
        """Add scan result to table"""
        try:
            self.scan_results.append(result)

            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            # IP Address
            ip_item = QTableWidgetItem(result.get('ip', 'Unknown'))
            self.results_table.setItem(row, 0, ip_item)

            # Hostname
            hostname = result.get('hostname', 'N/A')
            hostname_item = QTableWidgetItem(hostname)
            self.results_table.setItem(row, 1, hostname_item)

            # Status
            is_up = result.get('is_up', False)
            status_item = QTableWidgetItem("Online" if is_up else "Offline")
            if is_up:
                status_item.setForeground(QColor("#27ae60"))
            else:
                status_item.setForeground(QColor("#e74c3c"))
            self.results_table.setItem(row, 2, status_item)

            # Open Ports
            ports = result.get('open_ports', [])
            ports_text = f"{len(ports)}" if ports else "0"
            ports_item = QTableWidgetItem(ports_text)
            self.results_table.setItem(row, 3, ports_item)

            # Services
            services = result.get('services', [])
            services_text = ", ".join(services[:3])  # Show first 3 services
            if len(services) > 3:
                services_text += f" +{len(services)-3} more"
            services_item = QTableWidgetItem(services_text)
            self.results_table.setItem(row, 4, services_item)

            # Vulnerabilities
            vulns = result.get('vulnerabilities', [])
            vuln_count = len(vulns)
            vuln_item = QTableWidgetItem(str(vuln_count))
            if vuln_count > 0:
                vuln_item.setForeground(QColor("#e74c3c"))
            self.results_table.setItem(row, 5, vuln_item)

            # ML Risk Score and Level
            ml_analysis = result.get('ml_analysis', {})
            if ml_analysis:
                risk_score = ml_analysis.get('risk_score', 0)
                risk_level = ml_analysis.get('risk_level', 'Unknown')

                # ML Risk Score
                score_item = QTableWidgetItem(f"{risk_score:.2f}")
                self.results_table.setItem(row, 6, score_item)

                # Risk Level (color-coded)
                level_item = QTableWidgetItem(risk_level)
                if risk_level == "Critical":
                    level_item.setBackground(QColor("#e74c3c"))
                    level_item.setForeground(QColor("white"))
                elif risk_level == "High":
                    level_item.setBackground(QColor("#e67e22"))
                    level_item.setForeground(QColor("white"))
                elif risk_level == "Medium":
                    level_item.setBackground(QColor("#f39c12"))
                    level_item.setForeground(QColor("white"))
                else:  # Low
                    level_item.setBackground(QColor("#27ae60"))
                    level_item.setForeground(QColor("white"))
                self.results_table.setItem(row, 7, level_item)
            else:
                self.results_table.setItem(row, 6, QTableWidgetItem("N/A"))
                self.results_table.setItem(row, 7, QTableWidgetItem("N/A"))

            # Device Type (from ML or manual detection)
            device_type = result.get('device_type', 'Unknown')
            device_item = QTableWidgetItem(device_type)
            self.results_table.setItem(row, 8, device_item)

            self.log_status(f"✓ Added: {result.get('ip')} - {risk_level if ml_analysis else 'No ML data'}")

            # Emit signal to notify main window of discovered device
            self.device_discovered.emit(result)

        except Exception as e:
            self.log_error(f"Error adding result: {str(e)}")

    def update_results_summary(self):
        """Update results summary label"""
        total = len(self.scan_results)
        online = sum(1 for r in self.scan_results if r.get('is_up', False))

        critical = 0
        high = 0

        for result in self.scan_results:
            ml_analysis = result.get('ml_analysis', {})
            if ml_analysis:
                risk_level = ml_analysis.get('risk_level', '')
                if risk_level == 'Critical':
                    critical += 1
                elif risk_level == 'High':
                    high += 1

        self.results_summary.setText(
            f"Total Devices: {total} | Online: {online} | Critical Risk: {critical} | High Risk: {high}"
        )

    def clear_results(self):
        """Clear all scan results"""
        reply = QMessageBox.question(
            self, "Clear Results",
            "Are you sure you want to clear all scan results?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.results_table.setRowCount(0)
            self.scan_results.clear()
            self.status_text.clear()
            self.progress_bar.setValue(0)
            self.update_results_summary()
            self.log_status("Results cleared")

    def export_results(self):
        """Export scan results to JSON/CSV"""
        if not self.scan_results:
            QMessageBox.information(self, "No Data", "No scan results to export.")
            return

        # Ask user for file format
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Scan Results",
            f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json);;CSV Files (*.csv)"
        )

        if not filename:
            return

        try:
            if filename.endswith('.json'):
                # Export as JSON
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({
                        'scan_date': datetime.now().isoformat(),
                        'total_targets': len(self.scan_results),
                        'results': self.scan_results
                    }, f, indent=2)

            elif filename.endswith('.csv'):
                # Export as CSV
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'IP Address', 'Hostname', 'Status', 'Open Ports', 'Services',
                        'Vulnerabilities', 'ML Risk Score', 'Risk Level', 'Device Type'
                    ])

                    for result in self.scan_results:
                        ml_analysis = result.get('ml_analysis', {})
                        writer.writerow([
                            result.get('ip', ''),
                            result.get('hostname', ''),
                            'Online' if result.get('is_up') else 'Offline',
                            len(result.get('open_ports', [])),
                            ', '.join(result.get('services', [])),
                            len(result.get('vulnerabilities', [])),
                            f"{ml_analysis.get('risk_score', 0):.2f}" if ml_analysis else 'N/A',
                            ml_analysis.get('risk_level', 'N/A') if ml_analysis else 'N/A',
                            result.get('device_type', 'Unknown')
                        ])

            QMessageBox.information(self, "Export Successful", f"Results exported to:\n{filename}")
            self.log_status(f"Exported results to {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export results:\n{str(e)}")
            self.log_error(f"Export failed: {str(e)}")

    def log_status(self, message: str):
        """Log status message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")

        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def log_error(self, message: str):
        """Log error message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] ❌ ERROR: {message}")

        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


if __name__ == "__main__":
    """Standalone test mode"""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = NetworkScannerTab()
    window.setWindowTitle("OT Security Scanner - Test Mode")
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())

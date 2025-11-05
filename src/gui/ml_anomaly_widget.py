"""
Enhanced ML Detection Widget with Real-Time Monitoring
Hybrid ML models + IDS/IPS capabilities for OT/ICS networks
"""

import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QGroupBox,
    QProgressBar, QTextEdit, QHeaderView, QMessageBox, QSpinBox,
    QApplication
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

# Import ML security system
try:
    from ml.models.hybrid_security_models import HybridSecuritySystem
    from ml.monitoring.realtime_monitor import RealtimeMonitor, Alert
    ML_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML Security System not available: {e}")
    ML_SYSTEM_AVAILABLE = False


class MLAnomalyWidget(QWidget):
    """Enhanced widget for real-time ML-powered threat detection"""

    # Signal for when alert is detected (can be connected to notifications)
    alert_detected = pyqtSignal(object)  # Alert object

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize ML system
        self.ml_system = None
        self.monitor = None
        self.monitoring_active = False

        if ML_SYSTEM_AVAILABLE:
            try:
                self.ml_system = HybridSecuritySystem()
                self.monitor = RealtimeMonitor(ml_system=self.ml_system)
                # Register callback for alerts
                self.monitor.register_alert_callback(self.on_alert_received)
            except Exception as e:
                print(f"Error initializing ML system: {e}")

        self.init_ui()

        # Update timer for statistics
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
    
    def init_ui(self):
        """Initialize comprehensive ML Detection UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header with monitoring controls
        header_layout = QHBoxLayout()
        header = QLabel("🤖 Real-Time ML Threat Detection & IDS/IPS")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        header_layout.addWidget(header)
        header_layout.addStretch()

        # Monitoring controls
        self.start_monitor_btn = QPushButton("▶ Start Monitoring")
        self.start_monitor_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.start_monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.start_monitor_btn.clicked.connect(self.start_monitoring)
        header_layout.addWidget(self.start_monitor_btn)

        self.stop_monitor_btn = QPushButton("⬛ Stop Monitoring")
        self.stop_monitor_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.stop_monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
        self.stop_monitor_btn.setEnabled(False)
        header_layout.addWidget(self.stop_monitor_btn)

        # Train Models button
        self.train_models_btn = QPushButton("🎓 Train Models")
        self.train_models_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.train_models_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.train_models_btn.clicked.connect(self.train_models)
        header_layout.addWidget(self.train_models_btn)

        # Attack Simulation button
        self.attack_sim_btn = QPushButton("🔥 Run Attack Simulations")
        self.attack_sim_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.attack_sim_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.attack_sim_btn.clicked.connect(self.run_attack_simulations)
        header_layout.addWidget(self.attack_sim_btn)

        layout.addLayout(header_layout)

        # Status and Statistics
        stats_group = QGroupBox("Monitoring Status & Statistics")
        stats_layout = QVBoxLayout()

        # Status label
        self.status_label = QLabel("⚠ Monitoring: Stopped")
        self.status_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #e67e22; padding: 5px;")
        stats_layout.addWidget(self.status_label)

        # Statistics grid
        stats_grid = QHBoxLayout()

        self.devices_stat = self.create_stat_widget("Active Devices", "0", "#3498db")
        self.anomalies_stat = self.create_stat_widget("Anomalies", "0", "#e67e22")
        self.threats_stat = self.create_stat_widget("Threats", "0", "#e74c3c")
        self.alerts_stat = self.create_stat_widget("Total Alerts", "0", "#9b59b6")

        stats_grid.addWidget(self.devices_stat)
        stats_grid.addWidget(self.anomalies_stat)
        stats_grid.addWidget(self.threats_stat)
        stats_grid.addWidget(self.alerts_stat)

        stats_layout.addLayout(stats_grid)

        # Uptime and packet stats
        runtime_layout = QHBoxLayout()
        self.uptime_label = QLabel("Uptime: 00:00:00")
        self.packets_label = QLabel("Packets Analyzed: 0")
        runtime_layout.addWidget(self.uptime_label)
        runtime_layout.addStretch()
        runtime_layout.addWidget(self.packets_label)
        stats_layout.addLayout(runtime_layout)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Live Alerts Table
        alerts_group = QGroupBox("Live Alerts & Detections")
        alerts_layout = QVBoxLayout()

        # Alert filter and controls
        alert_controls = QHBoxLayout()
        alert_controls.addWidget(QLabel("Show:"))

        self.severity_filter = QPushButton("All Severities ▼")
        self.severity_filter.setStyleSheet("text-align: left; padding: 5px;")
        alert_controls.addWidget(self.severity_filter)

        alert_controls.addStretch()

        clear_alerts_btn = QPushButton("🗑 Clear Alerts")
        clear_alerts_btn.clicked.connect(self.clear_alerts)
        alert_controls.addWidget(clear_alerts_btn)

        export_alerts_btn = QPushButton("💾 Export Alerts")
        export_alerts_btn.clicked.connect(self.export_alerts)
        alert_controls.addWidget(export_alerts_btn)

        alerts_layout.addLayout(alert_controls)

        # Alerts table
        self.alerts_table = QTableWidget(0, 6)
        self.alerts_table.setHorizontalHeaderLabels([
            "Time", "Severity", "Type", "Device IP", "Description", "Details"
        ])

        header = self.alerts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Severity
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Device IP
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Description
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)           # Details

        self.alerts_table.setAlternatingRowColors(True)
        self.alerts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.alerts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        alerts_layout.addWidget(self.alerts_table)

        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)

        # Detection Details Log
        log_group = QGroupBox("Detection Log")
        log_layout = QVBoxLayout()

        self.detection_log = QTextEdit()
        self.detection_log.setReadOnly(True)
        self.detection_log.setMaximumHeight(150)
        self.detection_log.setStyleSheet("background: #2c3e50; color: #ecf0f1; font-family: monospace;")
        self.detection_log.setPlaceholderText("Detection events will appear here...")
        log_layout.addWidget(self.detection_log)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        self.setLayout(layout)

        # Check ML system availability
        if not ML_SYSTEM_AVAILABLE or not self.ml_system:
            self.start_monitor_btn.setEnabled(False)
            self.status_label.setText("⚠ ML System Not Available")
            self.status_label.setStyleSheet("color: #e74c3c; padding: 5px;")
            self.log_detection("ERROR: ML Security System not loaded. Please check installation.")

    def create_stat_widget(self, label: str, value: str, color: str) -> QGroupBox:
        """Create a statistics display widget"""
        group = QGroupBox(label)
        layout = QVBoxLayout()

        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color}; padding: 10px;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        group.setLayout(layout)

        # Store reference for updates
        if label == "Active Devices":
            self.devices_value_label = value_label
        elif label == "Anomalies":
            self.anomalies_value_label = value_label
        elif label == "Threats":
            self.threats_value_label = value_label
        elif label == "Total Alerts":
            self.alerts_value_label = value_label

        return group

    def start_monitoring(self):
        """Start real-time monitoring"""
        if not self.monitor:
            QMessageBox.warning(self, "ML System Unavailable",
                              "ML Security System is not available. Please check installation.")
            return

        try:
            # Start monitoring with 30-second interval
            self.monitor.start_monitoring(scan_interval=30)

            self.monitoring_active = True
            self.start_monitor_btn.setEnabled(False)
            self.stop_monitor_btn.setEnabled(True)

            self.status_label.setText("✓ Monitoring: Active")
            self.status_label.setStyleSheet("color: #27ae60; padding: 5px;")

            self.log_detection("✓ Real-time monitoring started")
            self.log_detection(f"• Hybrid ML models: Loaded")
            self.log_detection(f"• IDS/IPS engine: Active")
            self.log_detection(f"• Scan interval: 30 seconds")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start monitoring:\n{str(e)}")
            self.log_detection(f"ERROR: Failed to start monitoring: {e}")

    def stop_monitoring(self):
        """Stop real-time monitoring"""
        if self.monitor:
            self.monitor.stop_monitoring()

        self.monitoring_active = False
        self.start_monitor_btn.setEnabled(True)
        self.stop_monitor_btn.setEnabled(False)

        self.status_label.setText("⚠ Monitoring: Stopped")
        self.status_label.setStyleSheet("color: #e67e22; padding: 5px;")

        self.log_detection("⬛ Real-time monitoring stopped")

    def on_alert_received(self, alert: Alert):
        """Callback when alert is received from monitor"""
        try:
            # Add to alerts table
            row = self.alerts_table.rowCount()
            self.alerts_table.insertRow(row)

            # Time
            time_str = alert.timestamp.strftime("%H:%M:%S")
            self.alerts_table.setItem(row, 0, QTableWidgetItem(time_str))

            # Severity (color-coded)
            severity_item = QTableWidgetItem(alert.severity)
            severity_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            if alert.severity == "CRITICAL":
                severity_item.setBackground(QColor("#e74c3c"))
                severity_item.setForeground(QColor("white"))
            elif alert.severity == "HIGH":
                severity_item.setBackground(QColor("#e67e22"))
                severity_item.setForeground(QColor("white"))
            elif alert.severity == "MEDIUM":
                severity_item.setBackground(QColor("#f39c12"))
                severity_item.setForeground(QColor("white"))
            else:  # LOW
                severity_item.setBackground(QColor("#3498db"))
                severity_item.setForeground(QColor("white"))
            self.alerts_table.setItem(row, 1, severity_item)

            # Type
            self.alerts_table.setItem(row, 2, QTableWidgetItem(alert.alert_type))

            # Device IP
            self.alerts_table.setItem(row, 3, QTableWidgetItem(alert.device_ip))

            # Description
            self.alerts_table.setItem(row, 4, QTableWidgetItem(alert.description))

            # Details
            details_str = ", ".join([f"{k}: {v}" for k, v in alert.details.items()][:3])
            self.alerts_table.setItem(row, 5, QTableWidgetItem(details_str))

            # Scroll to latest alert
            self.alerts_table.scrollToBottom()

            # Log to detection log
            self.log_detection(f"🚨 [{alert.severity}] {alert.alert_type}: {alert.description}")

            # Emit signal
            self.alert_detected.emit(alert)

        except Exception as e:
            print(f"Error adding alert to table: {e}")

    def update_display(self):
        """Update statistics display"""
        if not self.monitor or not self.monitoring_active:
            return

        try:
            stats = self.monitor.get_statistics()

            # Update stat widgets
            self.devices_value_label.setText(str(stats.get('active_devices', 0)))
            self.anomalies_value_label.setText(str(stats.get('anomalies_detected', 0)))
            self.threats_value_label.setText(str(stats.get('threats_detected', 0)))
            self.alerts_value_label.setText(str(stats.get('total_alerts', 0)))

            # Update uptime
            uptime = stats.get('uptime_formatted', '00:00:00')
            self.uptime_label.setText(f"Uptime: {uptime}")

            # Update packets
            packets = stats.get('packets_analyzed', 0)
            self.packets_label.setText(f"Packets Analyzed: {packets:,}")

        except Exception as e:
            print(f"Error updating display: {e}")

    def clear_alerts(self):
        """Clear all alerts from table"""
        reply = QMessageBox.question(
            self, "Clear Alerts",
            "Are you sure you want to clear all alerts?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.alerts_table.setRowCount(0)
            self.log_detection("🗑 Alerts cleared")

    def export_alerts(self):
        """Export alerts to JSON file"""
        if not self.monitor:
            return

        try:
            from PyQt6.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Alerts",
                f"ml_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json)"
            )

            if filename:
                self.monitor.export_alerts(filename)
                self.log_detection(f"✓ Alerts exported to {filename}")
                QMessageBox.information(self, "Export Successful",
                                      f"Alerts exported to:\n{filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export alerts:\n{str(e)}")

    def log_detection(self, message: str):
        """Log message to detection log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.detection_log.append(f"[{timestamp}] {message}")

        # Auto-scroll to bottom
        scrollbar = self.detection_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def establish_baseline(self, devices: list):
        """Establish baseline from discovered devices"""
        if not self.monitor:
            return

        try:
            self.monitor.baseline.establish_baseline(devices)
            self.log_detection(f"✓ Baseline established: {len(devices)} devices")
            QMessageBox.information(self, "Baseline Established",
                                  f"Network baseline established with {len(devices)} devices.\n\n"
                                  "The system will now learn normal behavior and detect anomalies.")

        except Exception as e:
            self.log_detection(f"ERROR: Failed to establish baseline: {e}")

    def analyze_scanned_device(self, device_data: dict):
        """Analyze a newly scanned device with ML models"""
        if not self.monitor:
            return

        try:
            self.monitor.analyze_device(device_data.get('ip_address') or device_data.get('ip'),
                                       device_data)
        except Exception as e:
            print(f"Error analyzing device: {e}")

    def train_models(self):
        """Train ML models with synthetic OT/ICS training data"""
        if not self.ml_system:
            QMessageBox.warning(self, "ML System Error",
                              "ML system not initialized. Cannot train models.")
            return

        # Confirm training
        reply = QMessageBox.question(
            self, "Train ML Models",
            "This will train all ML models with synthetic OT/ICS security data:\n\n"
            "• Anomaly Detection (Isolation Forest + Random Forest)\n"
            "• Threat Classification (XGBoost)\n"
            "• Vulnerability Prediction (Decision Trees)\n"
            "• Protocol Analysis (K-Means + SVM)\n\n"
            "Training may take 10-30 seconds. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            from PyQt6.QtCore import QThread, pyqtSignal
            from PyQt6.QtWidgets import QProgressDialog

            # Create progress dialog
            progress = QProgressDialog("Training ML models...", None, 0, 0, self)
            progress.setWindowTitle("Model Training")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()

            # Import training data generator
            try:
                from src.ml.training.training_data_generator import OTTrainingDataGenerator
            except ImportError:
                # Try relative import
                import sys
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                from src.ml.training.training_data_generator import OTTrainingDataGenerator

            # Generate training data
            self.log_detection("⏳ Generating training dataset...")
            generator = OTTrainingDataGenerator()
            training_data = generator.generate_complete_training_set()

            progress.setLabelText("Training models...")
            QApplication.processEvents()

            # Train models
            self.log_detection("⏳ Training ML models...")
            results = self.ml_system.train_all_models(training_data)

            progress.close()

            # Show results
            if results.get('overall_success'):
                self.log_detection("✓ All models trained successfully!")

                # Check training status
                training_status = self.ml_system.is_trained()
                status_text = "\n".join([
                    f"• {model.replace('_', ' ').title()}: {'✓ Trained' if status else '✗ Not Trained'}"
                    for model, status in training_status.items()
                ])

                QMessageBox.information(self, "Training Successful",
                                      f"All ML models trained successfully!\n\n{status_text}\n\n"
                                      "You can now use the models for real-time threat detection.")
            else:
                self.log_detection("⚠ Some models failed to train")

                # Show which models failed
                failures = [
                    model.replace('_', ' ').title()
                    for model, result in results.items()
                    if model != 'overall_success' and not result.get('success')
                ]

                QMessageBox.warning(self, "Training Incomplete",
                                  f"Some models failed to train:\n\n" +
                                  "\n".join([f"• {f}" for f in failures]) +
                                  "\n\nCheck console output for details.")

        except Exception as e:
            self.log_detection(f"ERROR: Training failed: {e}")
            QMessageBox.critical(self, "Training Error",
                               f"Failed to train models:\n{str(e)}\n\n"
                               "Check console output for details.")
            import traceback
            traceback.print_exc()

    def run_attack_simulations(self):
        """Run attack simulations to test IDS/IPS detection"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, QLabel, QTextEdit
        from PyQt6.QtCore import QThread, pyqtSignal

        # Show attack selection dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Attack Simulation Suite")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout()

        # Warning label
        warning = QLabel(
            "⚠️  <b>AUTHORIZED USE ONLY</b><br><br>"
            "This will simulate real attack patterns against <b>127.0.0.1</b> (localhost).<br>"
            "Select which attack types to simulate:"
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("padding: 10px; background: #fff3cd; border-left: 4px solid #ffc107;")
        layout.addWidget(warning)

        # Attack checkboxes
        attacks = {
            'portscan': '🔍 Port Scanning (Reconnaissance)',
            'dos': '💥 DoS Attack (SYN Flood)',
            'fuzzing': '🔨 Service Fuzzing',
            'exploit': '⚡ Exploitation Attempts',
            'backdoor': '🚪 Backdoor Communication',
            'recon': '🌐 Network Reconnaissance'
        }

        checkboxes = {}
        for key, label in attacks.items():
            cb = QCheckBox(label)
            cb.setChecked(True)
            checkboxes[key] = cb
            layout.addWidget(cb)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # Get selected attacks
        selected = [key for key, cb in checkboxes.items() if cb.isChecked()]

        if not selected:
            QMessageBox.information(self, "No Attacks Selected",
                                  "Please select at least one attack type to simulate.")
            return

        # Run simulations in background thread
        class AttackSimulationThread(QThread):
            log_signal = pyqtSignal(str)
            finished_signal = pyqtSignal(dict)

            def __init__(self, attacks_to_run):
                super().__init__()
                self.attacks_to_run = attacks_to_run
                self.results = {}

            def run(self):
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'tests' / 'security'))

                try:
                    from attack_simulator import (
                        PortScanSimulator, SynFloodSimulator, ServiceFuzzingSimulator,
                        ExploitSimulator, BackdoorSimulator, ReconnaissanceSimulator
                    )

                    simulators = {
                        'portscan': (PortScanSimulator, {'target_ip': '127.0.0.1', 'port_range': (20, 100)}),
                        'dos': (SynFloodSimulator, {'target_ip': '127.0.0.1', 'target_port': 80, 'duration': 5}),
                        'fuzzing': (ServiceFuzzingSimulator, {'target_ip': '127.0.0.1', 'target_port': 80}),
                        'exploit': (ExploitSimulator, {'target_ip': '127.0.0.1', 'target_port': 80}),
                        'backdoor': (BackdoorSimulator, {'target_ip': '127.0.0.1', 'target_port': 4444}),
                        'recon': (ReconnaissanceSimulator, {'target_network': '127.0.0.1/29'}),
                    }

                    for attack_key in self.attacks_to_run:
                        if attack_key not in simulators:
                            continue

                        SimClass, kwargs = simulators[attack_key]
                        self.log_signal.emit(f"🔥 Running {attack_key} simulation...")

                        sim = SimClass(**kwargs)
                        result = sim.simulate()
                        self.results[attack_key] = result

                        self.log_signal.emit(f"✓ {attack_key} complete")
                        import time
                        time.sleep(1)

                    self.finished_signal.emit(self.results)

                except Exception as e:
                    self.log_signal.emit(f"✗ Error: {str(e)}")
                    import traceback
                    traceback.print_exc()

        # Create and start thread
        self.sim_thread = AttackSimulationThread(selected)
        self.sim_thread.log_signal.connect(self.log_detection)

        def on_simulations_complete(results):
            total = len(results)
            self.log_detection(f"\n✓ Completed {total} attack simulations")
            self.log_detection("⚠️  Check alerts table for detected threats!")

            QMessageBox.information(
                self, "Simulations Complete",
                f"Completed {total} attack simulations.\n\n"
                f"Check the 'Live Alerts' table above to see which attacks were detected.\n\n"
                f"Attack types simulated: {', '.join(results.keys())}"
            )

        self.sim_thread.finished_signal.connect(on_simulations_complete)

        self.log_detection("\n" + "=" * 50)
        self.log_detection("🔥 STARTING ATTACK SIMULATIONS")
        self.log_detection("=" * 50)
        self.log_detection(f"Selected: {', '.join(selected)}")
        self.log_detection("Target: 127.0.0.1 (localhost)")
        self.log_detection("")

        self.sim_thread.start()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = MLAnomalyWidget()
    widget.setWindowTitle("ML Threat Detection & IDS/IPS")
    widget.resize(1200, 800)
    widget.show()
    sys.exit(app.exec())

"""
Protocol Analysis Tab UI - PyQt6 Version
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTextEdit, QSplitter,
    QMessageBox, QApplication, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import protocol analyzer
try:
    from scanner.protocol_analyzer import IndustrialProtocolAnalyzer, ProtocolInfo
except ImportError:
    try:
        from src.scanner.protocol_analyzer import IndustrialProtocolAnalyzer, ProtocolInfo
    except ImportError:
        print("Error: Cannot import protocol_analyzer module")
        IndustrialProtocolAnalyzer = None
        ProtocolInfo = None


class ProtocolAnalysisTab(QWidget):
    """Protocol Analysis Tab Widget"""

    def __init__(self, parent=None):
        """Initialize the Protocol Analysis Tab"""
        super().__init__(parent)

        # Initialize analyzer
        if IndustrialProtocolAnalyzer:
            self.analyzer = IndustrialProtocolAnalyzer()
        else:
            self.analyzer = None

        self.protocols = []
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header with statistics
        header_widget = self.create_header()
        layout.addWidget(header_widget)

        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Protocol table
        protocol_table_widget = self.create_protocol_table()
        splitter.addWidget(protocol_table_widget)

        # Protocol details panel
        details_panel = self.create_details_panel()
        splitter.addWidget(details_panel)

        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)

    def create_header(self):
        """Create header with statistics"""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Title
        title = QLabel("🔬 Industrial Protocol Analysis")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
        layout.addWidget(title)

        layout.addStretch()

        # Statistics cards
        self.total_protocols_label = QLabel("Total: 0")
        self.active_protocols_label = QLabel("Active: 0")
        self.critical_protocols_label = QLabel("Critical: 0")

        for label in [self.total_protocols_label, self.active_protocols_label, self.critical_protocols_label]:
            label.setStyleSheet("""
                QLabel {
                    background-color: #37474F;
                    color: white;
                    padding: 8px 15px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            layout.addWidget(label)

        # Analyze button
        analyze_btn = QPushButton("🔍 Analyze Protocols")
        analyze_btn.clicked.connect(self.analyze_protocols)
        analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(analyze_btn)

        return widget

    def create_protocol_table(self):
        """Create protocol table"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Table
        self.protocol_table = QTableWidget()
        self.protocol_table.setColumnCount(9)
        self.protocol_table.setHorizontalHeaderLabels([
            'Protocol', 'Device IP', 'Hostname', 'Port', 'Status',
            'Version', 'Response Time', 'Risk Level', 'Security Issues'
        ])

        # Table styling
        self.protocol_table.setStyleSheet("""
            QTableWidget {
                background-color: #263238;
                color: white;
                gridline-color: #37474F;
                border: none;
            }
            QHeaderView::section {
                background-color: #37474F;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #1976D2;
            }
        """)

        self.protocol_table.horizontalHeader().setStretchLastSection(True)
        self.protocol_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.protocol_table.itemSelectionChanged.connect(self.on_protocol_selected)

        layout.addWidget(self.protocol_table)

        return widget

    def create_details_panel(self):
        """Create protocol details panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Details label
        details_label = QLabel("Protocol Details:")
        details_label.setStyleSheet("font-weight: bold; color: white;")
        layout.addWidget(details_label)

        # Details text area
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #263238;
                color: white;
                border: 1px solid #37474F;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        self.details_text.setPlaceholderText("Select a protocol to view details...")

        layout.addWidget(self.details_text)

        return widget

    def analyze_protocols(self):
        """Trigger protocol analysis"""
        if not self.analyzer:
            QMessageBox.critical(self, "Error", "Protocol analyzer not initialized!")
            return

        # Get main window safely
        main_window = None
        parent = self.parent()

        # Traverse up to find MainWindow
        while parent is not None:
            if hasattr(parent, 'get_discovered_devices'):
                main_window = parent
                break
            parent = parent.parent() if hasattr(parent, 'parent') else None

        if not main_window:
            QMessageBox.warning(self, "No Devices", "Cannot access device list. Please run a network scan first!")
            return

        devices = main_window.get_discovered_devices()

        if not devices:
            QMessageBox.warning(self, "No Devices", "No devices found. Run a network scan first!")
            return

        # Analyze protocols
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.protocols = self.analyzer.analyze_devices(devices)
        except Exception as e:
            QMessageBox.critical(self, "Analysis Error", f"Error during protocol analysis:\n{str(e)}")
            self.protocols = []
        finally:
            QApplication.restoreOverrideCursor()

        # Update UI
        self.update_protocol_table()
        self.update_statistics()

        QMessageBox.information(
            self,
            "Analysis Complete",
            f"Found {len(self.protocols)} industrial protocols across {len(devices)} devices"
        )

    def update_protocol_table(self):
        """Update protocol table with results"""
        self.protocol_table.setRowCount(0)

        for protocol in self.protocols:
            row = self.protocol_table.rowCount()
            self.protocol_table.insertRow(row)

            # Get risk level
            protocol_data = self.analyzer.INDUSTRIAL_PROTOCOLS.get(protocol.protocol_name, {})
            risk_level = protocol_data.get('risk_level', 'Unknown')

            # Populate row
            items = [
                protocol.protocol_name,
                protocol.device_ip,
                protocol.device_hostname,
                str(protocol.port),
                protocol.status,
                protocol.protocol_version,
                protocol.details.get('response_time', 'N/A'),
                risk_level,
                str(len(protocol.security_issues))
            ]

            for col, value in enumerate(items):
                item = QTableWidgetItem(value)
                self.protocol_table.setItem(row, col, item)

            # Color code by risk level
            if risk_level == 'Critical':
                color = QColor(211, 47, 47, 100)  # Red
            elif risk_level == 'High':
                color = QColor(255, 152, 0, 100)  # Orange
            else:
                color = QColor(76, 175, 80, 100)  # Green

            for col in range(self.protocol_table.columnCount()):
                item = self.protocol_table.item(row, col)
                if item:
                    item.setBackground(color)

    def update_statistics(self):
        """Update statistics labels"""
        if not self.analyzer:
            return

        stats = self.analyzer.get_protocol_statistics()

        self.total_protocols_label.setText(f"Total: {stats['total_protocols']}")
        self.active_protocols_label.setText(f"Active: {stats['active_protocols']}")
        self.critical_protocols_label.setText(f"Critical: {stats['critical_count']}")

    def on_protocol_selected(self):
        """Handle protocol selection"""
        selected_rows = self.protocol_table.selectionModel().selectedRows()

        if not selected_rows:
            return

        row = selected_rows[0].row()

        if row < len(self.protocols):
            protocol = self.protocols[row]
            self.show_protocol_details(protocol)

    def show_protocol_details(self, protocol):
        """Show detailed information about selected protocol"""
        if not self.analyzer:
            return

        protocol_data = self.analyzer.INDUSTRIAL_PROTOCOLS.get(protocol.protocol_name, {})

        details_html = f"""
        <h2 style="color: #2196F3;">{protocol.protocol_name}</h2>
        <hr>
        
        <h3>Device Information:</h3>
        <ul>
            <li><b>IP Address:</b> {protocol.device_ip}</li>
            <li><b>Hostname:</b> {protocol.device_hostname}</li>
            <li><b>Port:</b> {protocol.port}</li>
            <li><b>Vendor:</b> {protocol.vendor}</li>
            <li><b>Status:</b> <span style="color: {'#4CAF50' if protocol.status == 'Active' else '#FFA726'}">{protocol.status}</span></li>
        </ul>
        
        <h3>Protocol Details:</h3>
        <ul>
            <li><b>Description:</b> {protocol_data.get('description', 'N/A')}</li>
            <li><b>Category:</b> {protocol_data.get('category', 'N/A')}</li>
            <li><b>Risk Level:</b> <span style="color: {'#D32F2F' if protocol_data.get('risk_level') == 'Critical' else '#FF9800'}">{protocol_data.get('risk_level', 'Unknown')}</span></li>
            <li><b>Version:</b> {protocol.protocol_version}</li>
            <li><b>Response Time:</b> {protocol.details.get('response_time', 'N/A')}</li>
        </ul>
        
        <h3>Features:</h3>
        <ul>
            {''.join(f"<li>{feature}</li>" for feature in protocol.details.get('features', []))}
        </ul>
        
        <h3 style="color: #FF5722;">Security Issues ({len(protocol.security_issues)}):</h3>
        <ul style="color: #FF5722;">
            {''.join(f"<li>{issue}</li>" for issue in protocol.security_issues)}
        </ul>
        
        <hr>
        <p><i>Last analyzed: {protocol.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</i></p>
        """

        self.details_text.setHtml(details_html)

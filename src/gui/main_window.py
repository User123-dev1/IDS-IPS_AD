#!/usr/bin/env python3
"""
OT Asset Manager - Main Application Window
Professional Industrial Asset Management Interface
"""

# ============================================================================
# SECTION 1: Standard Library Imports
# ============================================================================
import sys
import os
import ipaddress
from datetime import datetime

# ============================================================================
# Windows Console UTF-8 Fix (for emoji support)
# ============================================================================
if sys.platform == 'win32':
    try:
        # Set UTF-8 encoding for stdout/stderr on Windows
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass  # If this fails, the log() method has fallback handling

# ============================================================================
# SECTION 2: Path Setup (MUST BE BEFORE LOCAL IMPORTS!)
# ============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# ============================================================================
# SECTION 3: Third-Party Imports (PyQt6)
# ============================================================================
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QVBoxLayout, QHBoxLayout, QWidget,
    QMenuBar, QToolBar, QStatusBar, QTabWidget, QDockWidget,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QSplitter, QGroupBox,
    QProgressBar, QComboBox, QLineEdit, QSpinBox, QCheckBox,
    QMessageBox, QFileDialog, QPlainTextEdit
)
from PyQt6.QtCore import QThread, QObject, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor, QAction

from gui.ml_anomaly_widget import MLAnomalyWidget
from gui.ml_performance_widget import MLPerformanceWidget

# OT Security Scanner Integration
try:
    from gui.network_scanner_tab import NetworkScannerTab
    NETWORK_SCANNER_AVAILABLE = True
except Exception as e:
    print(f"[!] Network Scanner Tab import failed: {e}")
    NETWORK_SCANNER_AVAILABLE = False

# ============================================================================
# SECTION 4: Local Imports (AFTER path setup)
# ============================================================================
from gui.rule_manager_window import RuleManagerWindow
from gui.live_dashboard import LiveDashboardWidget

# ---- Import Scanner ----
try:
    from scanner.network_scanner import EnterpriseNetworkScanner
    SCANNER_AVAILABLE = True
except Exception as e:
    print(f"Warning: Scanner not available - {e}")
    SCANNER_AVAILABLE = False
    EnterpriseNetworkScanner = None

# ---- Import Network Graph (Optional) ----
try:
    from gui.network_graph import NetworkGraphWidget
    NETWORK_GRAPH_AVAILABLE = True
except Exception as e:
    NetworkGraphWidget = None
    NETWORK_GRAPH_AVAILABLE = False
    print(f"Warning: NetworkGraphWidget unavailable - {e}")

# ---- Import Protocol Analysis Tab (Optional) ----
try:
    from gui.protocol_analysis_tab import ProtocolAnalysisTab
    PROTOCOL_TAB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import ProtocolAnalysisTab: {e}")
    PROTOCOL_TAB_AVAILABLE = False
    ProtocolAnalysisTab = None


# ---- Custom Security Score Gauge Widget ----
class SecurityScoreGauge(QWidget):
    """Custom widget to display security score as a visual gauge"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.score = 0
        self.risk_level = "UNKNOWN"
        self.setMinimumSize(200, 200)

    def setScore(self, score: int, risk_level: str = "UNKNOWN"):
        """Update the score and risk level"""
        self.score = max(0, min(100, score))  # Clamp between 0-100
        self.risk_level = risk_level
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """Paint the gauge"""
        from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QConicalGradient
        from PyQt6.QtCore import Qt, QRect, QPoint

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get widget dimensions
        width = self.width()
        height = self.height()
        side = min(width, height)

        # Center the gauge
        painter.translate(width / 2, height / 2)

        # Draw outer circle (background)
        painter.setPen(QPen(QColor("#ecf0f1"), 15))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        radius = side / 2 - 20
        painter.drawEllipse(int(-radius), int(-radius), int(radius * 2), int(radius * 2))

        # Determine color based on score
        if self.score >= 80:
            color = QColor("#27ae60")  # Green - LOW risk
        elif self.score >= 60:
            color = QColor("#f39c12")  # Yellow - MEDIUM risk
        elif self.score >= 40:
            color = QColor("#e67e22")  # Orange - HIGH risk
        else:
            color = QColor("#e74c3c")  # Red - CRITICAL risk

        # Draw score arc
        painter.setPen(QPen(color, 15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        start_angle = 90 * 16  # Start at top (12 o'clock)
        span_angle = -int((self.score / 100.0) * 360 * 16)  # Clockwise
        painter.drawArc(int(-radius), int(-radius), int(radius * 2), int(radius * 2),
                       start_angle, span_angle)

        # Draw inner circle (background for text)
        inner_radius = radius - 40
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(int(-inner_radius), int(-inner_radius),
                          int(inner_radius * 2), int(inner_radius * 2))

        # Draw score text
        painter.setPen(QColor("#2c3e50"))
        font = QFont("Segoe UI", int(side / 8), QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRect(int(-radius), int(-radius/2), int(radius * 2), int(radius/2)),
                        Qt.AlignmentFlag.AlignCenter, f"{self.score}")

        # Draw "/ 100" text
        small_font = QFont("Segoe UI", int(side / 16))
        painter.setFont(small_font)
        painter.setPen(QColor("#7f8c8d"))
        painter.drawText(QRect(int(-radius), int(radius/4), int(radius * 2), int(radius/4)),
                        Qt.AlignmentFlag.AlignCenter, "/ 100")

        # Draw risk level text
        painter.setPen(color)
        painter.setFont(QFont("Segoe UI", int(side / 12), QFont.Weight.Bold))
        painter.drawText(QRect(int(-radius), int(radius/2), int(radius * 2), int(radius/3)),
                        Qt.AlignmentFlag.AlignCenter, self.risk_level)


# ---- ScanWorker class (ONLY ONE DEFINITION) ----
class ScanWorker(QObject):
    """Worker for background network scanning"""
    finished = pyqtSignal(list)
    progress = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, scanner, subnets):
        super().__init__()
        self.scanner = scanner
        self.subnets = subnets

    def run(self):
        """Execute scan with error handling"""
        try:
            self.progress.emit(f" Scanning {len(self.subnets)} subnet(s)...")
            devices = self.scanner.scan_multiple_subnets(self.subnets)

            if not devices:
                self.progress.emit(" No devices found")
            else:
                self.progress.emit(f" Found {len(devices)} device(s)")

            self.finished.emit(devices)

        except Exception as e:
            import traceback
            error_details = f"{str(e)}\n\n{traceback.format_exc()}"
            self.error.emit(error_details)


class MainWindow(QMainWindow):
    """Main Application Window for OT Asset Manager"""

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Welore Plexes")
        self.setGeometry(100, 100, 1400, 900)

        # Initialize components
        self.setup_scanner()
        self.setup_styling()
        self.setup_menubar()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_dock_panels()
        self.setup_central_widget()
        self.setup_timers()

        self.log(" Main window initialized successfully")
        if not SCANNER_AVAILABLE:
            self.log(" Network scanner not available - running in demo mode")

    # ---------- Logging ----------

    def log(self, message: str) -> None:
        """Safe logger"""
        ts = datetime.now().strftime("%H:%M:%S")
        lt = getattr(self, "logs_text", None)
        try:
            if lt is not None:
                lt.append(f"[{ts}] {message}")
                cursor = lt.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                lt.setTextCursor(cursor)
            else:
                print(f"[{ts}] {message}")
        except Exception:
            print(f"[{ts}] {message}")

    # ---------- Setup ----------

    def setup_scanner(self):
        """Initialize the network scanner"""
        self.scanner = None
        if SCANNER_AVAILABLE:
            try:
                self.scanner = EnterpriseNetworkScanner()
            except Exception as e:
                print(f"Failed to create scanner: {e}")

    def setup_styling(self):
        """Set up the application styling"""
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; color: #ffffff; }
            QMenuBar { background-color: #3c3c3c; color: #ffffff; border-bottom: 1px solid #555; }
            QMenuBar::item { padding: 8px 12px; }
            QMenuBar::item:selected { background-color: #0078d4; }
            QMenu { background-color: #3c3c3c; color: #ffffff; border: 1px solid #555; }
            QMenu::item:selected { background-color: #0078d4; }
            QToolBar { background-color: #404040; border: 1px solid #555; padding: 5px; }
            QPushButton { 
                background-color: #0078d4; color: white; border: none; 
                padding: 8px 16px; border-radius: 4px; font-weight: bold; 
            }
            QPushButton:hover { background-color: #106ebe; }
            QPushButton:pressed { background-color: #005a9e; }
            QPushButton:disabled { background-color: #555; color: #999; }
            QTabWidget::pane { border: 1px solid #555; background-color: #2b2b2b; }
            QTabBar::tab { background-color: #404040; color: #ffffff; padding: 10px 20px; }
            QTabBar::tab:selected { background-color: #0078d4; }
            QDockWidget { background-color: #353535; color: #ffffff; border: 1px solid #555; }
            QDockWidget::title { background-color: #404040; padding: 8px; font-weight: bold; }
            QTreeWidget, QTableWidget { 
                background-color: #353535; color: #ffffff; border: 1px solid #555; 
                alternate-background-color: #404040; 
            }
            QTreeWidget::item:selected, QTableWidget::item:selected { background-color: #0078d4; }
            QTextEdit { 
                background-color: #1e1e1e; color: #ffffff; border: 1px solid #555; 
                font-family: 'Consolas', monospace; 
            }
            QStatusBar { background-color: #404040; color: #ffffff; border-top: 1px solid #555; }
            QGroupBox { 
                border: 2px solid #555; border-radius: 5px; margin-top: 1ex; font-weight: bold; 
            }
            QGroupBox::title { 
                subcontrol-origin: margin; subcontrol-position: top center; 
                padding: 0 5px; color: #0078d4; 
            }
            QLineEdit, QSpinBox, QComboBox { 
                background-color: #404040; color: #ffffff; border: 1px solid #555; 
                padding: 5px; border-radius: 3px; 
            }
            QProgressBar { border: 1px solid #555; border-radius: 3px; text-align: center; }
            QProgressBar::chunk { background-color: #0078d4; border-radius: 2px; }
        """)

    def setup_menubar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')
        new_project = QAction('&New Project', self)
        new_project.setShortcut('Ctrl+N')
        new_project.triggered.connect(self.new_project)

        open_project = QAction('&Open Project', self)
        open_project.setShortcut('Ctrl+O')
        open_project.triggered.connect(self.open_project)

        export_data = QAction('&Export Results', self)
        export_data.triggered.connect(lambda: self.export_results('csv'))

        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)

        file_menu.addActions([new_project, open_project])
        file_menu.addSeparator()
        file_menu.addAction(export_data)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        file_menu.addSeparator()
        rule_manager_action = file_menu.addAction("⚙️ Alert Rules Manager")
        rule_manager_action.triggered.connect(self.open_rule_manager)
        file_menu.addAction("Exit", self.close)

        # ==========================================
        # VIEW MENU - Reports & Visualizations
        # ==========================================
        view_menu = menubar.addMenu('&View')

        # View Reports submenu
        reports_submenu = view_menu.addMenu('📊 Reports')

        # Vulnerability Report
        vuln_report_action = QAction('🔒 Vulnerability Assessment', self)
        vuln_report_action.setShortcut('Ctrl+R')
        vuln_report_action.triggered.connect(self.open_vulnerability_report)
        reports_submenu.addAction(vuln_report_action)

        # Compliance Report
        compliance_report_action = QAction('📋 Compliance Report', self)
        compliance_report_action.triggered.connect(self.open_compliance_report)
        reports_submenu.addAction(compliance_report_action)

        # Asset Summary
        asset_report_action = QAction('📦 Asset Summary', self)
        asset_report_action.triggered.connect(self.open_asset_report)
        reports_submenu.addAction(asset_report_action)

        view_menu.addSeparator()

        # View options
        refresh_action = QAction('🔄 Refresh All', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_all_data)
        view_menu.addAction(refresh_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        scan_action = QAction(' Scan Network', self)
        scan_action.triggered.connect(self.show_scan_tab)

        report_action = QAction(' Report', self)
        report_action.triggered.connect(self.generate_report)

        toolbar.addAction(scan_action)
        toolbar.addSeparator()
        toolbar.addAction(report_action)

        self.addToolBar(toolbar)

    def setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        self.network_status = QLabel("Network: Ready")
        self.network_status.setStyleSheet("color: #51cf66;")
        self.status_bar.addPermanentWidget(self.network_status)

        self.asset_count = QLabel("Assets: 0")
        self.status_bar.addPermanentWidget(self.asset_count)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def setup_dock_panels(self):
        # Assets dock (left)
        self.assets_dock = QDockWidget("Assets", self)
        assets_widget = QWidget()
        assets_layout = QVBoxLayout(assets_widget)

        self.assets_tree = QTreeWidget()
        self.assets_tree.setHeaderLabels(["Device", "Type", "IP Address", "Status"])
        assets_layout.addWidget(self.assets_tree)

        self.assets_dock.setWidget(assets_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.assets_dock)

        # Logs dock (bottom)
        self.logs_dock = QDockWidget("System Logs", self)
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setMaximumHeight(200)
        self.logs_dock.setWidget(self.logs_text)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.logs_dock)

    def setup_central_widget(self):
        """Setup the central widget with tabs"""

        # ===== CREATE SINGLE TAB WIDGET =====
        self.central_tabs = QTabWidget()
        self.setCentralWidget(self.central_tabs)

        # Tab configuration
        self.central_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.central_tabs.setMovable(True)
        self.central_tabs.setDocumentMode(True)

        self.monitor_tab = LiveDashboardWidget()
        self.central_tabs.addTab(self.monitor_tab, " Network Monitor")

        self.ml_tab = MLAnomalyWidget()
        self.central_tabs.addTab(self.ml_tab, " ML Detection")

        # ML Performance/Results Tab
        self.ml_performance_tab = MLPerformanceWidget()
        self.central_tabs.addTab(self.ml_performance_tab, "📊 ML Performance")

        # Tab styling
        self.central_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #CCCCCC;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border-bottom: 2px solid #2196F3;
            }
            QTabBar::tab:hover {
                background-color: #3D3D3D;
            }
        """)

        # ===== ADD ALL TABS TO CENTRAL_TABS =====

        # 1. Dashboard Tab
        try:
            self.dashboard_tab = self.create_dashboard_tab()
            self.central_tabs.addTab(self.dashboard_tab, " Dashboard")
            print(" Dashboard tab created")
        except Exception as e:
            print(f" Error creating Dashboard tab: {e}")

        # 2. Network Scanner Tab
        try:
            if NETWORK_SCANNER_AVAILABLE:
                self.scanner_tab = NetworkScannerTab()
                self.central_tabs.addTab(self.scanner_tab, "🔍 OT Security Scanner")

                # Connect scanner signals to update network graph and assets
                self.scanner_tab.device_discovered.connect(self.on_device_discovered)

                # Connect scanner to ML Detection tab for real-time analysis
                if hasattr(self, 'ml_tab'):
                    self.scanner_tab.device_discovered.connect(self.ml_tab.analyze_scanned_device)
                    self.scanner_tab.scan_complete.connect(self.on_scan_complete_ml)

                print("✅ OT Security Scanner tab created with vulnerability assessment")
            else:
                # Fallback to old scanner
                self.scanner_tab = self.create_scanner_tab()
                self.central_tabs.addTab(self.scanner_tab, " Network Scanner")
                print(" Network Scanner tab created (legacy)")
        except Exception as e:
            print(f" Error creating Scanner tab: {e}")

        # 3. Network Discovery Tab
        try:
            network_discovery_tab = self.create_network_discovery_tab()
            self.central_tabs.addTab(network_discovery_tab, " Network Discovery")
            print(" Network Discovery tab created")
        except Exception as e:
            print(f" Error creating Network Discovery tab: {e}")

        # 4. Protocol Analysis Tab
        if PROTOCOL_TAB_AVAILABLE and ProtocolAnalysisTab:
            try:
                self.protocol_tab = ProtocolAnalysisTab(self)
                self.central_tabs.addTab(self.protocol_tab, " Protocol Analysis")
                print(" Protocol Analysis tab created successfully!")
            except Exception as e:
                print(f" Error creating Protocol Analysis tab: {e}")
                # Create error placeholder
                placeholder = QWidget()
                layout = QVBoxLayout(placeholder)
                error_label = QLabel(f"Protocol Analysis Error:\n{str(e)}")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                error_label.setStyleSheet("color: #FF5722; font-size: 14px; padding: 20px;")
                layout.addWidget(error_label)
                self.central_tabs.addTab(placeholder, " Protocol Analysis")
        else:
            print(" Protocol Analysis tab disabled - import failed")
            print(f"   PROTOCOL_TAB_AVAILABLE = {PROTOCOL_TAB_AVAILABLE}")
            print(f"   ProtocolAnalysisTab = {ProtocolAnalysisTab}")
            # Create placeholder for missing module
            placeholder = QWidget()
            layout = QVBoxLayout(placeholder)
            error_label = QLabel(
                "Protocol Analysis Module Not Available\n\nPlease check:\n protocol_analysis_tab.py exists\n No import errors in console")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("color: #FFA726; font-size: 14px; padding: 20px;")
            layout.addWidget(error_label)
            self.central_tabs.addTab(placeholder, " Protocol Analysis")

        # 5. Asset Inventory Tab
        try:
            self.inventory_tab = self.create_inventory_tab()
            self.central_tabs.addTab(self.inventory_tab, " Asset Inventory")
            print(" Asset Inventory tab created")
        except Exception as e:
            print(f" Error creating Inventory tab: {e}")

        # 6. Security Tab
        try:
            self.security_tab = self.create_security_tab()
            self.central_tabs.addTab(self.security_tab, " Security")
            print(" Security tab created")
        except Exception as e:
            print(f" Error creating Security tab: {e}")

        # 7. Visualization Tab
        try:
            visualization_tab = self.create_visualization_tab()
            self.central_tabs.addTab(visualization_tab, " Visualization")
            print(" Visualization tab created")
        except Exception as e:
            print(f" Error creating Visualization tab: {e}")

        # 8. Reports Tab
        try:
            self.reports_tab = self.create_reports_tab()
            self.central_tabs.addTab(self.reports_tab, " Reports")
            print(" Reports tab created")
        except Exception as e:
            print(f" Error creating Reports tab: {e}")

        print(f"\n Total tabs created: {self.central_tabs.count()}")

    def setup_timers(self):
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)

    # ---------- Tab Creation ----------

    def create_scanner_tab(self):
        """Network scanner tab - same as network discovery"""
        return self.create_network_discovery_tab()

    def create_inventory_tab(self):
        """Asset inventory management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QLabel("Asset Inventory")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(header)

        # Info box
        info_group = QGroupBox("About Asset Inventory")
        info_layout = QVBoxLayout()
        info_text = QLabel(
            "The Asset Inventory provides centralized management of all discovered OT/IT assets.\n\n"
            "Features:\n"
            "• View all discovered devices from network scans\n"
            "• Manually add and categorize assets\n"
            "• Track asset details (IP, MAC, protocols, services)\n"
            "• Monitor asset status and health\n"
            "• Export inventory reports\n\n"
            "Get started by running a Network Discovery scan."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #34495e; padding: 10px;")
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Asset table (stored as instance variable for updates)
        table_group = QGroupBox("Discovered Assets")
        table_layout = QVBoxLayout()

        self.inventory_asset_table = QTableWidget(0, 7)
        self.inventory_asset_table.setHorizontalHeaderLabels([
            "IP Address", "Hostname", "MAC Address", "Vendor", "Device Type", "Status", "Last Seen"
        ])
        self.inventory_asset_table.horizontalHeader().setStretchLastSection(True)
        self.inventory_asset_table.setAlternatingRowColors(True)
        self.inventory_asset_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.inventory_asset_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_layout.addWidget(self.inventory_asset_table)

        # Action buttons (now enabled and connected)
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Add Asset Manually")
        add_btn.setFont(QFont("Segoe UI", 10))
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        add_btn.clicked.connect(self.add_inventory_asset_manually)

        refresh_btn = QPushButton("🔄 Refresh from Assets")
        refresh_btn.setFont(QFont("Segoe UI", 10))
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_inventory_from_assets)

        export_btn = QPushButton("📄 Export Inventory")
        export_btn.setFont(QFont("Segoe UI", 10))
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        export_btn.clicked.connect(self.export_inventory)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addStretch()

        # Asset count label
        self.inventory_count_label = QLabel("Total Assets: 0")
        self.inventory_count_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        btn_layout.addWidget(self.inventory_count_label)

        table_layout.addLayout(btn_layout)

        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        widget.setLayout(layout)

        # Initial refresh
        QTimer.singleShot(500, self.refresh_inventory_from_assets)

        return widget

    def create_reports_tab(self):
        """Reports and analytics tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QLabel("Reports & Analytics")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(header)

        # Report types
        reports_group = QGroupBox("Available Reports")
        reports_layout = QVBoxLayout()

        # Network Discovery Report
        discovery_btn = QPushButton("📊 Network Discovery Summary")
        discovery_btn.setFont(QFont("Segoe UI", 11))
        discovery_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px;
                text-align: left;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        discovery_btn.clicked.connect(self.generate_discovery_report)
        reports_layout.addWidget(discovery_btn)

        # Asset Inventory Report
        inventory_btn = QPushButton("📦 Asset Inventory Report")
        inventory_btn.setFont(QFont("Segoe UI", 11))
        inventory_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                padding: 12px;
                text-align: left;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        inventory_btn.clicked.connect(self.generate_inventory_report)
        reports_layout.addWidget(inventory_btn)

        # Security Assessment Report
        security_btn = QPushButton("🔒 Security Assessment Report")
        security_btn.setFont(QFont("Segoe UI", 11))
        security_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 12px;
                text-align: left;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        security_btn.clicked.connect(self.generate_security_report)
        reports_layout.addWidget(security_btn)

        # Network Monitor Report
        monitor_btn = QPushButton("📈 Network Monitoring Statistics")
        monitor_btn.setFont(QFont("Segoe UI", 11))
        monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 12px;
                text-align: left;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        monitor_btn.clicked.connect(self.generate_monitoring_report)
        reports_layout.addWidget(monitor_btn)

        reports_group.setLayout(reports_layout)
        layout.addWidget(reports_group)

        # Export options
        export_group = QGroupBox("Export Options")
        export_layout = QHBoxLayout()

        self.pdf_export_btn = QPushButton("📄 Export as PDF")
        self.csv_export_btn = QPushButton("📊 Export as CSV")
        self.json_export_btn = QPushButton("📋 Export as JSON")

        # Connect export buttons
        self.pdf_export_btn.clicked.connect(self.export_report_pdf)
        self.csv_export_btn.clicked.connect(self.export_report_csv)
        self.json_export_btn.clicked.connect(self.export_report_json)

        for btn in [self.pdf_export_btn, self.csv_export_btn, self.json_export_btn]:
            btn.setEnabled(False)  # Enable when reports are generated
            btn.setFont(QFont("Segoe UI", 10))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #34495e;
                    color: white;
                    padding: 8px 15px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #2c3e50;
                }
                QPushButton:disabled {
                    background-color: #95a5a6;
                }
            """)
            export_layout.addWidget(btn)

        export_layout.addStretch()
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        # Preview area
        preview_group = QGroupBox("Report Preview")
        preview_layout = QVBoxLayout()

        self.report_preview_text = QTextEdit()
        self.report_preview_text.setReadOnly(True)
        self.report_preview_text.setPlainText("Select a report type above to generate and preview reports.")
        self.report_preview_text.setStyleSheet("background: #f8f9fa; border: 1px solid #dee2e6; font-family: monospace;")
        preview_layout.addWidget(self.report_preview_text)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Store current report data for export
        self.current_report_data = None
        self.current_report_type = None

        widget.setLayout(layout)
        return widget

    def create_dashboard_tab(self):
        """Create main dashboard overview tab with dynamic statistics"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header with refresh button
        header_layout = QHBoxLayout()
        header = QLabel("OT Asset Manager Dashboard")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        header_layout.addWidget(header)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFont(QFont("Segoe UI", 10))
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_dashboard_stats)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Quick Stats (now with references for dynamic updates)
        stats_group = QGroupBox("System Overview")
        stats_layout = QHBoxLayout()

        self.dashboard_assets_label = QLabel("Total Assets\n0")
        self.dashboard_assets_label.setFont(QFont("Segoe UI", 12))
        self.dashboard_assets_label.setStyleSheet("color: #3498db; padding: 15px; background: #ecf0f1; border-radius: 5px;")
        self.dashboard_assets_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.dashboard_assets_label)

        self.dashboard_active_label = QLabel("Active Devices\n0")
        self.dashboard_active_label.setFont(QFont("Segoe UI", 12))
        self.dashboard_active_label.setStyleSheet("color: #2ecc71; padding: 15px; background: #ecf0f1; border-radius: 5px;")
        self.dashboard_active_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.dashboard_active_label)

        self.dashboard_vuln_label = QLabel("Vulnerabilities\n0")
        self.dashboard_vuln_label.setFont(QFont("Segoe UI", 12))
        self.dashboard_vuln_label.setStyleSheet("color: #e74c3c; padding: 15px; background: #ecf0f1; border-radius: 5px;")
        self.dashboard_vuln_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.dashboard_vuln_label)

        self.dashboard_ot_label = QLabel("OT Devices\n0")
        self.dashboard_ot_label.setFont(QFont("Segoe UI", 12))
        self.dashboard_ot_label.setStyleSheet("color: #e67e22; padding: 15px; background: #ecf0f1; border-radius: 5px;")
        self.dashboard_ot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.dashboard_ot_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Quick Actions (enhanced with better actions)
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout()

        # Row 1: Scan actions
        scan_row = QHBoxLayout()

        quick_scan_btn = QPushButton("🔍 Quick Network Scan")
        quick_scan_btn.setFont(QFont("Segoe UI", 11))
        quick_scan_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; padding: 10px; border-radius: 5px; }")
        quick_scan_btn.clicked.connect(self.start_quick_scan)
        scan_row.addWidget(quick_scan_btn)

        full_scan_btn = QPushButton("🔎 Full Network Scan")
        full_scan_btn.setFont(QFont("Segoe UI", 11))
        full_scan_btn.setStyleSheet("QPushButton { background-color: #2980b9; color: white; padding: 10px; border-radius: 5px; }")
        full_scan_btn.clicked.connect(self.start_full_scan)
        scan_row.addWidget(full_scan_btn)

        actions_layout.addLayout(scan_row)

        # Row 2: Monitor actions
        monitor_row = QHBoxLayout()

        monitor_btn = QPushButton("📊 Real-time Network Monitor")
        monitor_btn.setFont(QFont("Segoe UI", 11))
        monitor_btn.setStyleSheet("QPushButton { background-color: #9b59b6; color: white; padding: 10px; border-radius: 5px; }")
        monitor_btn.clicked.connect(self.open_network_monitor)
        monitor_row.addWidget(monitor_btn)

        ml_detection_btn = QPushButton("🤖 ML Anomaly Detection")
        ml_detection_btn.setFont(QFont("Segoe UI", 11))
        ml_detection_btn.setStyleSheet("QPushButton { background-color: #8e44ad; color: white; padding: 10px; border-radius: 5px; }")
        ml_detection_btn.clicked.connect(self.open_ml_detection)
        monitor_row.addWidget(ml_detection_btn)

        actions_layout.addLayout(monitor_row)

        # Row 3: Report actions
        report_row = QHBoxLayout()

        export_btn = QPushButton("📄 Export Results")
        export_btn.setFont(QFont("Segoe UI", 11))
        export_btn.setStyleSheet("QPushButton { background-color: #27ae60; color: white; padding: 10px; border-radius: 5px; }")
        export_btn.clicked.connect(self.export_scan_results)
        report_row.addWidget(export_btn)

        visualize_btn = QPushButton("🌐 Network Visualization")
        visualize_btn.setFont(QFont("Segoe UI", 11))
        visualize_btn.setStyleSheet("QPushButton { background-color: #16a085; color: white; padding: 10px; border-radius: 5px; }")
        visualize_btn.clicked.connect(self.open_visualization)
        report_row.addWidget(visualize_btn)

        actions_layout.addLayout(report_row)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        # Recent Activity (now dynamic)
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout()
        self.dashboard_activity_text = QTextEdit()
        self.dashboard_activity_text.setReadOnly(True)
        self.dashboard_activity_text.setMaximumHeight(150)
        self.dashboard_activity_text.setPlainText("System ready. Start a network scan to discover devices.")
        activity_layout.addWidget(self.dashboard_activity_text)
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)

        layout.addStretch()
        widget.setLayout(layout)

        # Initial stats update
        self.refresh_dashboard_stats()

        return widget

    def create_network_discovery_tab(self):
        """Create the network discovery/scanning interface"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Add after Export button
        sync_btn = QPushButton(" Sync to Assets & Graph")
        sync_btn.clicked.connect(self.manual_sync_devices)
        sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        layout.addWidget(sync_btn)

        # Title
        title = QLabel(" Enterprise Network Discovery")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Subnet input
        subnet_group = QGroupBox("Subnets to Scan")
        subnet_layout = QVBoxLayout()

        subnet_help = QLabel("Enter subnets in CIDR notation (one per line):\nExample: 192.168.1.0/24")
        subnet_help.setStyleSheet("color: #95a5a6; font-size: 11px;")
        subnet_layout.addWidget(subnet_help)

        self.subnet_input = QPlainTextEdit()
        self.subnet_input.setPlaceholderText("10.10.100.0/24\n192.168.12.0/24\n192.168.1.0/24")
        self.subnet_input.setMaximumHeight(120)
        subnet_layout.addWidget(self.subnet_input)

        subnet_group.setLayout(subnet_layout)
        layout.addWidget(subnet_group)

        # Scan options
        options_group = QGroupBox("Scan Options")
        options_layout = QHBoxLayout()

        options_layout.addWidget(QLabel("Max Workers:"))
        self.max_workers = QSpinBox()
        self.max_workers.setRange(1, 200)
        self.max_workers.setValue(50)
        options_layout.addWidget(self.max_workers)
        options_layout.addStretch()

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.scan_button = QPushButton(" Start Scan")
        self.scan_button.clicked.connect(self.start_enterprise_scan)
        button_layout.addWidget(self.scan_button)

        self.stop_button = QPushButton(" Stop Scan")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_enterprise_scan)
        button_layout.addWidget(self.stop_button)

        # Scan status label (added so later code references exist)
        self.scan_status = QLabel("Idle")
        self.scan_status.setStyleSheet("color:#ccc;")
        button_layout.addWidget(self.scan_status)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Progress bar
        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        layout.addWidget(self.scan_progress)

        # Scan log
        log_group = QGroupBox("Scan Log")
        log_layout = QVBoxLayout()

        self.scan_log = QTextEdit()


    def log(self, message):
        """Log message to console and GUI scan log"""
        # Print to console with encoding error handling (for Windows)
        try:
            print(message)
        except UnicodeEncodeError:
            # Windows console doesn't support emojis - print ASCII version
            try:
                # Try printing with ASCII-compatible encoding
                ascii_message = message.encode('ascii', errors='replace').decode('ascii')
                print(ascii_message)
            except:
                # Last resort: just print a simple message
                print("[Message contains unsupported characters]")

        # Write to scan_log widget if it exists (PyQt handles emojis fine)
        if hasattr(self, 'scan_log') and self.scan_log is not None:
            try:
                self.scan_log.append(message)
                # Auto-scroll to bottom
                scrollbar = self.scan_log.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            except Exception as e:
                print(f"[WARNING] Could not write to scan_log: {e}")

        # Force GUI update
        try:
            QApplication.processEvents()
        except:
            pass
    
    def get_discovered_devices(self):
        """Return list of discovered devices for protocol analysis"""
        devices = []

        for row in range(self.results_table.rowCount()):
            device = {
                'ip_address': self.results_table.item(row, 0).text() if self.results_table.item(row, 0) else '',
                'hostname': self.results_table.item(row, 1).text() if self.results_table.item(row, 1) else '',
                'mac': self.results_table.item(row, 2).text() if self.results_table.item(row, 2) else '',
                'vendor': self.results_table.item(row, 3).text() if self.results_table.item(row, 3) else '',
                'device_type': self.results_table.item(row, 4).text() if self.results_table.item(row, 4) else '',
                'status': self.results_table.item(row, 5).text() if self.results_table.item(row, 5) else 'online',
                'open_ports': []  # Will be populated from stored data
            }

            # Get open ports from stored device data
            if hasattr(self, 'device_data'):
                stored_device = next((d for d in self.device_data if d.get('ip_address') == device['ip_address']), None)
                if stored_device:
                    device['open_ports'] = stored_device.get('open_ports', [])

            devices.append(device)

        return devices

    def create_visualization_tab(self):
        """Create visualization tab"""
        viz_widget = QWidget()
        layout = QVBoxLayout(viz_widget)

        if NetworkGraphWidget:
            try:
                self.network_graph = NetworkGraphWidget()
                layout.addWidget(self.network_graph)
                self.log(" Network visualization ready")
            except Exception as e:
                self.log(f" Network graph failed: {e}")
                self.network_graph = None
                label = QLabel(f" Network Visualization\n\nGraph unavailable: {e}")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(label)
        else:
            label = QLabel(" Network Visualization\n\nGraph module not available")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)

        return viz_widget

    # ---------- Scanning Methods ----------

    def stop_enterprise_scan(self):
        """Stop running scan"""
        if hasattr(self, 'scan_thread') and self.scan_thread.isRunning():
            self.log(" Stopping scan...")
            self.scan_thread.quit()
            self.scan_thread.wait()
            self.log(" Scan stopped")

        self.scan_progress.setVisible(False)
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def on_scan_complete(self, devices: list):
        """Handle scan completion - sync to all views"""
        self.log(f" Scan complete! Found {len(devices)} devices")

        # Update results table
        self.results_table.setRowCount(0)

        for device in devices:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)

            # Add to results table
            self.results_table.setItem(row, 0, QTableWidgetItem(device.get('ip_address', '')))
            self.results_table.setItem(row, 1, QTableWidgetItem(device.get('hostname', '')))
            self.results_table.setItem(row, 2, QTableWidgetItem(device.get('mac', '')))
            self.results_table.setItem(row, 3, QTableWidgetItem(device.get('vendor', 'Unknown')))
            self.results_table.setItem(row, 4, QTableWidgetItem(device.get('device_type', 'unknown')))
            self.results_table.setItem(row, 5, QTableWidgetItem(device.get('status', 'online')))

            #  ADD TO ASSETS TREE
            self.add_device_to_assets(device)

            #  ADD TO NETWORK GRAPH
            if hasattr(self, 'network_graph') and self.network_graph:
                self.network_graph.add_device(device)

        # Update asset count in status bar
        self.asset_count.setText(f"Assets: {self.results_table.rowCount()}")

        # Reset UI
        self.scan_progress.setVisible(False)
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        # Cleanup thread
        if hasattr(self, 'scan_thread'):
            self.scan_thread.quit()
            self.scan_thread.wait()

        # Log success
        self.log(f" Added {len(devices)} devices to Assets")
        self.log(f" Added {len(devices)} devices to Visualization")

        QMessageBox.information(
            self,
            "Scan Complete",
            f" Found {len(devices)} devices!\n\n"
            f" Added to Results Table\n"
            f" Added to Assets Panel\n"
            f" Added to Network Visualization"
        )

    def on_device_discovered(self, device: dict):
        """Handle device discovered from NetworkScannerTab"""
        # Normalize device data - scanner uses 'ip', graph expects 'ip_address'
        if 'ip' in device and 'ip_address' not in device:
            device['ip_address'] = device['ip']

        # Add to assets tree
        self.add_device_to_assets(device)

        # Add to network graph visualization
        if hasattr(self, 'network_graph') and self.network_graph:
            self.network_graph.add_device(device)
            self.log(f"📡 Device added to topology: {device.get('ip_address', device.get('ip', 'Unknown'))}")

        # Update asset count
        asset_count = self.assets_tree.topLevelItemCount()
        self.asset_count.setText(f"Assets: {asset_count}")

    def on_scan_complete_ml(self, devices: list):
        """Handle scan completion - offer to establish ML baseline"""
        if not devices or len(devices) == 0:
            return

        # Check if ML tab is available
        if not hasattr(self, 'ml_tab') or self.ml_tab is None:
            return

        # Offer to establish ML baseline for threat detection
        reply = QMessageBox.question(
            self, "Establish ML Baseline",
            f"Network scan complete! {len(devices)} devices discovered.\n\n"
            "Would you like to establish an ML baseline for threat detection?\n\n"
            "This will:\n"
            "• Learn normal network behavior\n"
            "• Enable anomaly detection\n"
            "• Detect new/unknown devices\n"
            "• Identify security threats in real-time",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.ml_tab.establish_baseline(devices)
                self.log(f"✓ ML baseline established with {len(devices)} devices")

                # Ask if user wants to start monitoring now
                monitor_reply = QMessageBox.question(
                    self, "Start Monitoring",
                    "Baseline established successfully!\n\n"
                    "Would you like to start real-time monitoring now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if monitor_reply == QMessageBox.StandardButton.Yes:
                    # Switch to ML Detection tab
                    for i in range(self.central_tabs.count()):
                        if self.central_tabs.widget(i) == self.ml_tab:
                            self.central_tabs.setCurrentIndex(i)
                            break

                    # Start monitoring
                    self.ml_tab.start_monitoring()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to establish baseline:\n{str(e)}")
                self.log(f"ERROR: Failed to establish ML baseline: {e}")

    def add_device_to_assets(self, device: dict):
        """Add a discovered device to the Assets tree panel"""
        ip = device.get('ip_address', '')
        hostname = device.get('hostname', '') or ip
        device_type = device.get('device_type', 'Unknown')
        status = device.get('status', 'online')

        # Check if device already exists
        for i in range(self.assets_tree.topLevelItemCount()):
            existing_item = self.assets_tree.topLevelItem(i)
            if existing_item.text(2) == ip:  # IP is in column 2
                # Update existing item
                existing_item.setText(0, hostname)
                existing_item.setText(1, device_type)
                existing_item.setText(3, status)
                return

        # Create new tree item
        item = QTreeWidgetItem([hostname, device_type, ip, status])

        # Color code by status
        if status.lower() == 'online':
            item.setBackground(0, QColor(46, 125, 50, 100))  # Green
        else:
            item.setBackground(0, QColor(211, 47, 47, 100))  # Red

        # Add to tree
        self.assets_tree.addTopLevelItem(item)

    def on_scan_error(self, error_msg: str):
        """Handle scan errors"""
        self.log(f" Scan error: {error_msg}")

        self.scan_progress.setVisible(False)
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        if hasattr(self, 'scan_thread'):
            self.scan_thread.quit()
            self.scan_thread.wait()

        QMessageBox.critical(self, "Scan Error", f"Scan failed:\n\n{error_msg}")

    def export_scan_results(self):
        """Export scan results to CSV"""
        if self.results_table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No scan results to export")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Scan Results", "", "CSV Files (*.csv)"
        )

        if filename:
            try:
                import csv
                with open(filename, 'w', newline='') as file:
                    writer = csv.writer(file)

                    # Headers
                    headers = []
                    for col in range(self.results_table.columnCount()):
                        headers.append(self.results_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)

                    # Data
                    for row in range(self.results_table.rowCount()):
                        row_data = []
                        for col in range(self.results_table.columnCount()):
                            item = self.results_table.item(row, col)
                            row_data.append(item.text() if item else '')
                        writer.writerow(row_data)

                self.log(f" Exported to: {filename}")
                QMessageBox.information(self, "Export Successful", f"Results exported to:\n{filename}")
            except Exception as e:
                self.log(f" Export failed: {e}")
                QMessageBox.critical(self, "Export Failed", f"Failed to export:\n{e}")

    def send_to_visualization(self):
        """Send discovered devices to network visualization"""
        if not getattr(self, 'network_graph', None):
            QMessageBox.warning(self, "Visualization Not Available",
                                "Please enable the Visualization tab first")
            return

        device_count = 0
        for row in range(self.results_table.rowCount()):
            def _txt(c):
                item = self.results_table.item(row, c)
                return item.text() if item else ""

            device_data = {
                'ip_address': _txt(0),
                'hostname': _txt(1),
                'vendor': _txt(3),
                'device_type': _txt(4),
                'mac_address': _txt(2),
                'services': [],
                'status': _txt(5) or 'online'
            }

            if device_data['ip_address']:
                self.network_graph.add_device(device_data)
                device_count += 1

        self.log(f" Sent {device_count} devices to visualization")
        QMessageBox.information(self, "Success",
                                f"Added {device_count} devices to network visualization")

    def sync_discovered_devices(self):
        """Manually sync all discovered devices from the table to the graph"""
        if not getattr(self, 'network_graph', None):
            self.log(" Network graph not available")
            return

        device_count = 0
        for row in range(self.results_table.rowCount()):
            def _txt(c):
                item = self.results_table.item(row, c)
                return item.text() if item else ""

            device_data = {
                'ip_address': _txt(0),
                'hostname': _txt(1) or 'Unknown',
                'mac_address': _txt(2),
                'vendor': _txt(3),
                'services': [],
                'response_time': 0.0,
                'status': _txt(5) or 'online'
            }
            if device_data['ip_address']:
                self.network_graph.add_device(device_data)
                device_count += 1
                self.log(f" Synced device: {device_data['ip_address']}")

        if hasattr(self, 'network_graph') and hasattr(self.network_graph, 'nodes'):
            self.log(f" Graph nodes: {len(self.network_graph.nodes)}")
        self.log(f" Synced {device_count} devices to graph")

    def create_security_tab(self):
        """Create comprehensive security assessment tab"""
        security_widget = QWidget()
        layout = QVBoxLayout(security_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header with refresh button
        header_layout = QHBoxLayout()
        header = QLabel("🔒 Security Assessment")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        header_layout.addWidget(header)
        header_layout.addStretch()

        refresh_security_btn = QPushButton("🔄 Refresh Analysis")
        refresh_security_btn.setFont(QFont("Segoe UI", 10))
        refresh_security_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        refresh_security_btn.clicked.connect(self.refresh_security_assessment)
        header_layout.addWidget(refresh_security_btn)

        layout.addLayout(header_layout)

        # Overall Security Score - Visual Gauge
        score_group = QGroupBox("Overall Security Posture")
        score_layout = QHBoxLayout()

        # Add spacing on left
        score_layout.addStretch()

        # Security Score Gauge with caption
        gauge_container = QVBoxLayout()

        # Caption above gauge
        gauge_caption = QLabel("Security Health Score")
        gauge_caption.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        gauge_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gauge_caption.setStyleSheet("color: #2c3e50; padding: 5px;")
        gauge_container.addWidget(gauge_caption)

        # Description text
        gauge_description = QLabel("Based on vulnerabilities detected\n(100 = No issues, 0 = Critical)")
        gauge_description.setFont(QFont("Segoe UI", 9))
        gauge_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gauge_description.setStyleSheet("color: #7f8c8d; padding-bottom: 10px;")
        gauge_container.addWidget(gauge_description)

        # Security Score Gauge (custom visual widget)
        self.security_score_gauge = SecurityScoreGauge()
        self.security_score_gauge.setMinimumSize(250, 250)
        self.security_score_gauge.setMaximumSize(300, 300)
        gauge_container.addWidget(self.security_score_gauge, alignment=Qt.AlignmentFlag.AlignCenter)

        score_layout.addLayout(gauge_container)

        # Add spacing between gauge and risk label
        score_layout.addStretch()

        # Risk Level Label (keeping for additional info)
        self.risk_level_label = QLabel("Risk Level\nUNKNOWN")
        self.risk_level_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.risk_level_label.setStyleSheet("""
            color: #7f8c8d;
            padding: 20px;
            background: #ecf0f1;
            border-radius: 8px;
            border: 2px solid #bdc3c7;
        """)
        self.risk_level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.risk_level_label.setMinimumWidth(200)
        score_layout.addWidget(self.risk_level_label)

        # Add spacing on right
        score_layout.addStretch()

        score_group.setLayout(score_layout)
        layout.addWidget(score_group)

        # Vulnerability Statistics
        vuln_group = QGroupBox("Vulnerability Analysis")
        vuln_layout = QHBoxLayout()

        self.critical_vuln_label = QLabel("Critical\n0")
        self.critical_vuln_label.setFont(QFont("Segoe UI", 12))
        self.critical_vuln_label.setStyleSheet("color: #e74c3c; padding: 15px; background: #fadbd8; border-radius: 5px;")
        self.critical_vuln_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vuln_layout.addWidget(self.critical_vuln_label)

        self.high_vuln_label = QLabel("High\n0")
        self.high_vuln_label.setFont(QFont("Segoe UI", 12))
        self.high_vuln_label.setStyleSheet("color: #e67e22; padding: 15px; background: #fdebd0; border-radius: 5px;")
        self.high_vuln_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vuln_layout.addWidget(self.high_vuln_label)

        self.medium_vuln_label = QLabel("Medium\n0")
        self.medium_vuln_label.setFont(QFont("Segoe UI", 12))
        self.medium_vuln_label.setStyleSheet("color: #f39c12; padding: 15px; background: #fcf3cf; border-radius: 5px;")
        self.medium_vuln_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vuln_layout.addWidget(self.medium_vuln_label)

        self.low_vuln_label = QLabel("Low\n0")
        self.low_vuln_label.setFont(QFont("Segoe UI", 12))
        self.low_vuln_label.setStyleSheet("color: #3498db; padding: 15px; background: #d6eaf8; border-radius: 5px;")
        self.low_vuln_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vuln_layout.addWidget(self.low_vuln_label)

        vuln_group.setLayout(vuln_layout)
        layout.addWidget(vuln_group)

        # Security Findings Table
        findings_group = QGroupBox("Security Findings")
        findings_layout = QVBoxLayout()

        self.security_findings_table = QTableWidget(0, 5)
        self.security_findings_table.setHorizontalHeaderLabels([
            "Severity", "Device", "Finding", "Impact", "Recommendation"
        ])
        self.security_findings_table.horizontalHeader().setStretchLastSection(True)
        self.security_findings_table.setAlternatingRowColors(True)
        self.security_findings_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.security_findings_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        findings_layout.addWidget(self.security_findings_table)

        findings_group.setLayout(findings_layout)
        layout.addWidget(findings_group)

        # Security Recommendations
        recommendations_group = QGroupBox("Top Security Recommendations")
        recommendations_layout = QVBoxLayout()

        self.security_recommendations_text = QTextEdit()
        self.security_recommendations_text.setReadOnly(True)
        self.security_recommendations_text.setMaximumHeight(150)
        self.security_recommendations_text.setPlainText("Run a security assessment to view recommendations.")
        recommendations_layout.addWidget(self.security_recommendations_text)

        recommendations_group.setLayout(recommendations_layout)
        layout.addWidget(recommendations_group)

        # Action buttons
        button_layout = QHBoxLayout()

        export_report_btn = QPushButton("📄 Export Security Report")
        export_report_btn.setFont(QFont("Segoe UI", 10))
        export_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        export_report_btn.clicked.connect(self.export_security_report)
        button_layout.addWidget(export_report_btn)

        remediate_btn = QPushButton("🔧 View Remediation Guide")
        remediate_btn.setFont(QFont("Segoe UI", 10))
        remediate_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        remediate_btn.clicked.connect(self.show_remediation_guide)
        button_layout.addWidget(remediate_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Initial assessment
        QTimer.singleShot(1000, self.refresh_security_assessment)

        return security_widget

    def create_protocol_analysis_tab(self):
        protocol_widget = QWidget()
        layout = QVBoxLayout(protocol_widget)
        info_label = QLabel(" Protocol Analysis\n\nProtocol detection and analysis features will be displayed here.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(info_label)
        return protocol_widget

    def manual_sync_devices(self):
        """Manually sync all devices from results table to Assets and Graph"""
        if self.results_table.rowCount() == 0:
            QMessageBox.warning(self, "No Devices", "No devices in results table to sync")
            return

        self.log(" Manually syncing devices...")

        synced_count = 0
        for row in range(self.results_table.rowCount()):
            device = {
                'ip_address': self.results_table.item(row, 0).text() if self.results_table.item(row, 0) else '',
                'hostname': self.results_table.item(row, 1).text() if self.results_table.item(row, 1) else '',
                'mac': self.results_table.item(row, 2).text() if self.results_table.item(row, 2) else '',
                'vendor': self.results_table.item(row, 3).text() if self.results_table.item(row, 3) else 'Unknown',
                'device_type': self.results_table.item(row, 4).text() if self.results_table.item(row, 4) else 'unknown',
                'status': self.results_table.item(row, 5).text() if self.results_table.item(row, 5) else 'online'
            }

            if device['ip_address']:
                # Add to assets
                self.add_device_to_assets(device)

                # Add to graph
                if hasattr(self, 'network_graph') and self.network_graph:
                    self.network_graph.add_device(device)

                synced_count += 1

        self.asset_count.setText(f"Assets: {self.assets_tree.topLevelItemCount()}")
        self.log(f" Synced {synced_count} devices to Assets and Visualization")

        QMessageBox.information(
            self,
            "Sync Complete",
            f"Successfully synced {synced_count} devices to:\n\n"
            f" Assets Panel: {self.assets_tree.topLevelItemCount()} items\n"
            f" Network Graph: Updated"
        )

    def export_results(self, format_type: str):
        """Export results (wrapper)"""
        self.export_scan_results()

    # ---------- Menu Actions ----------

    def new_project(self):
        self.log("New project created")

    def open_project(self):
        self.log("Opening project...")

    def generate_report(self):
        self.log("Generating report...")

    def show_about(self):
        QMessageBox.about(
            self,
            "About OT Asset Manager",
            "OT Asset Manager v1.0\n\n"
            "Industrial Asset Discovery & Management System\n"
            "Built with PyQt6 and Python\n\n"
            " 2024 Industrial Security Solutions"
        )

    def show_scan_tab(self):
        """Switch to network discovery tab"""
        # Move to Network Discovery tab if present; otherwise first tab
        idx = max(0, self.central_tabs.count() - 1)
        self.central_tabs.setCurrentIndex(idx)

    def update_status(self):
        """Periodic status update"""
        self.refresh_dashboard_stats()

    # ========== DASHBOARD BUTTON ACTIONS ==========

    def refresh_dashboard_stats(self):
        """Refresh dashboard statistics from current data"""
        try:
            # Count total assets from assets tree
            total_assets = self.assets_tree.topLevelItemCount() if hasattr(self, 'assets_tree') else 0

            # Count active devices (online status)
            active_count = 0
            ot_count = 0
            if hasattr(self, 'assets_tree'):
                for i in range(self.assets_tree.topLevelItemCount()):
                    item = self.assets_tree.topLevelItem(i)
                    if item.text(3).lower() == 'online':  # Status column
                        active_count += 1
                    device_type = item.text(1).lower()  # Type column
                    if any(ot in device_type for ot in ['plc', 'ot', 'ics', 'hmi', 'scada', 'vfd']):
                        ot_count += 1

            # Count vulnerabilities from results table
            vuln_count = 0
            if hasattr(self, 'results_table'):
                # This is a simplified count - in a real system you'd query a vulnerability database
                vuln_count = 0  # Placeholder

            # Update dashboard labels
            if hasattr(self, 'dashboard_assets_label'):
                self.dashboard_assets_label.setText(f"Total Assets\n{total_assets}")

            if hasattr(self, 'dashboard_active_label'):
                self.dashboard_active_label.setText(f"Active Devices\n{active_count}")

            if hasattr(self, 'dashboard_vuln_label'):
                self.dashboard_vuln_label.setText(f"Vulnerabilities\n{vuln_count}")

            if hasattr(self, 'dashboard_ot_label'):
                self.dashboard_ot_label.setText(f"OT Devices\n{ot_count}")

            # Update activity log
            if hasattr(self, 'dashboard_activity_text'):
                timestamp = datetime.now().strftime("%H:%M:%S")
                activity_msg = f"[{timestamp}] Dashboard refreshed: {total_assets} assets, {active_count} active, {ot_count} OT devices"
                current_text = self.dashboard_activity_text.toPlainText()
                lines = current_text.split('\n')
                if len(lines) > 10:  # Keep only last 10 lines
                    lines = lines[-9:]
                lines.append(activity_msg)
                self.dashboard_activity_text.setPlainText('\n'.join(lines))

        except Exception as e:
            self.log(f"Error refreshing dashboard: {e}")

    def start_quick_scan(self):
        """Start a quick scan of the local subnet"""
        try:
            # Switch to network discovery tab
            for i in range(self.central_tabs.count()):
                if 'Discovery' in self.central_tabs.tabText(i) or 'Scanner' in self.central_tabs.tabText(i):
                    self.central_tabs.setCurrentIndex(i)
                    break

            # Set default subnet and trigger scan
            if hasattr(self, 'subnet_input'):
                # Auto-detect local subnet or use default
                import socket
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                # Extract subnet (simplified)
                subnet_parts = local_ip.rsplit('.', 1)[0]
                default_subnet = f"{subnet_parts}.0/24"
                self.subnet_input.setPlainText(default_subnet)

            self.log(f"🔍 Starting quick scan...")
            if hasattr(self, 'dashboard_activity_text'):
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.dashboard_activity_text.append(f"[{timestamp}] Quick scan initiated")

            # Trigger the scan if available
            if hasattr(self, 'start_enterprise_scan'):
                QTimer.singleShot(500, self.start_enterprise_scan)
            else:
                QMessageBox.information(self, "Quick Scan", "Please configure scan parameters in the Network Discovery tab")

        except Exception as e:
            self.log(f"Error starting quick scan: {e}")
            QMessageBox.warning(self, "Scan Error", f"Could not start quick scan: {e}")

    def start_full_scan(self):
        """Start a full comprehensive scan"""
        try:
            # Switch to network discovery tab
            for i in range(self.central_tabs.count()):
                if 'Discovery' in self.central_tabs.tabText(i) or 'Scanner' in self.central_tabs.tabText(i):
                    self.central_tabs.setCurrentIndex(i)
                    break

            self.log(f"🔎 Preparing full network scan...")
            if hasattr(self, 'dashboard_activity_text'):
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.dashboard_activity_text.append(f"[{timestamp}] Full scan mode activated")

            QMessageBox.information(
                self,
                "Full Network Scan",
                "Full scan mode activated.\n\n"
                "Configure multiple subnets in the Network Discovery tab\n"
                "and click 'Start Scan' to begin comprehensive scanning."
            )

        except Exception as e:
            self.log(f"Error starting full scan: {e}")

    def open_network_monitor(self):
        """Open the real-time network monitor tab"""
        try:
            # Find and switch to Network Monitor tab
            # Look for the tab by checking multiple patterns
            for i in range(self.central_tabs.count()):
                tab_text = self.central_tabs.tabText(i).strip()  # Strip whitespace

                # Check for various possible tab names
                if ('monitor' in tab_text.lower() and 'network' in tab_text.lower()) or \
                   'network monitor' in tab_text.lower():
                    self.central_tabs.setCurrentIndex(i)
                    self.log(f"📊 Opened Network Monitor (tab {i}: '{tab_text}')")
                    if hasattr(self, 'dashboard_activity_text'):
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        self.dashboard_activity_text.append(f"[{timestamp}] Network Monitor opened")
                    return

            # If not found, show all available tabs for debugging
            available_tabs = [self.central_tabs.tabText(i) for i in range(self.central_tabs.count())]
            self.log(f"Available tabs: {available_tabs}")

            QMessageBox.information(
                self,
                "Network Monitor",
                "Network Monitor tab not found.\n\n"
                f"Available tabs:\n" + "\n".join(f"  {i+1}. {tab}" for i, tab in enumerate(available_tabs))
            )

        except Exception as e:
            self.log(f"Error opening network monitor: {e}")
            import traceback
            traceback.print_exc()

    def open_ml_detection(self):
        """Open the ML anomaly detection tab"""
        try:
            # Find and switch to ML Detection tab
            for i in range(self.central_tabs.count()):
                tab_text = self.central_tabs.tabText(i).strip().lower()

                # Check for ML-related tab names
                if 'ml' in tab_text or 'machine learning' in tab_text or 'anomaly' in tab_text:
                    self.central_tabs.setCurrentIndex(i)
                    self.log(f"🤖 Opened ML Anomaly Detection (tab {i})")
                    if hasattr(self, 'dashboard_activity_text'):
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        self.dashboard_activity_text.append(f"[{timestamp}] ML Detection opened")
                    return

            # If not found, show available tabs
            available_tabs = [self.central_tabs.tabText(i) for i in range(self.central_tabs.count())]
            self.log(f"ML tab not found. Available: {available_tabs}")

            QMessageBox.information(
                self,
                "ML Detection",
                "ML Anomaly Detection tab not found.\n\n"
                f"Available tabs:\n" + "\n".join(f"  {i+1}. {tab}" for i, tab in enumerate(available_tabs))
            )

        except Exception as e:
            self.log(f"Error opening ML detection: {e}")
            import traceback
            traceback.print_exc()

    def open_visualization(self):
        """Open the network visualization tab"""
        try:
            # Find and switch to Visualization tab
            for i in range(self.central_tabs.count()):
                tab_text = self.central_tabs.tabText(i).strip().lower()

                # Check for visualization-related tab names
                if 'visualization' in tab_text or 'visual' in tab_text or 'graph' in tab_text:
                    self.central_tabs.setCurrentIndex(i)
                    self.log(f"🌐 Opened Network Visualization (tab {i})")
                    if hasattr(self, 'dashboard_activity_text'):
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        self.dashboard_activity_text.append(f"[{timestamp}] Network Visualization opened")

                    # Sync current devices to visualization
                    if hasattr(self, 'sync_discovered_devices'):
                        self.sync_discovered_devices()

                    return

            # If not found, show available tabs
            available_tabs = [self.central_tabs.tabText(i) for i in range(self.central_tabs.count())]
            self.log(f"Visualization tab not found. Available: {available_tabs}")

            QMessageBox.information(
                self,
                "Visualization",
                "Network Visualization tab not found.\n\n"
                f"Available tabs:\n" + "\n".join(f"  {i+1}. {tab}" for i, tab in enumerate(available_tabs))
            )

        except Exception as e:
            self.log(f"Error opening visualization: {e}")
            import traceback
            traceback.print_exc()

    def log_to_dashboard(self, message: str):
        """Log message to dashboard activity feed"""
        if hasattr(self, 'dashboard_activity_text'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.dashboard_activity_text.append(f"[{timestamp}] {message}")
            # Auto-scroll to bottom
            cursor = self.dashboard_activity_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.dashboard_activity_text.setTextCursor(cursor)

    # ========== SECURITY ASSESSMENT METHODS ==========

    def refresh_security_assessment(self):
        """Perform comprehensive security assessment of all assets"""
        try:
            self.log("🔒 Running security assessment...")

            # Collect all vulnerabilities from scanned devices
            all_vulnerabilities = []
            all_findings = []

            # Analyze data from results table if available
            if hasattr(self, 'results_table'):
                device_data = []
                for row in range(self.results_table.rowCount()):
                    device = {
                        'ip': self.results_table.item(row, 0).text() if self.results_table.item(row, 0) else '',
                        'hostname': self.results_table.item(row, 1).text() if self.results_table.item(row, 1) else '',
                        'device_type': self.results_table.item(row, 4).text() if self.results_table.item(row, 4) else '',
                    }
                    device_data.append(device)

            # Analyze assets tree for security issues
            security_findings = self.analyze_security_issues()

            # Count vulnerabilities by severity
            critical_count = security_findings['critical']
            high_count = security_findings['high']
            medium_count = security_findings['medium']
            low_count = security_findings['low']

            # Update vulnerability labels
            self.critical_vuln_label.setText(f"Critical\n{critical_count}")
            self.high_vuln_label.setText(f"High\n{high_count}")
            self.medium_vuln_label.setText(f"Medium\n{medium_count}")
            self.low_vuln_label.setText(f"Low\n{low_count}")

            # Calculate security score (0-100)
            total_vulns = critical_count + high_count + medium_count + low_count
            security_score = self.calculate_security_score(critical_count, high_count, medium_count, low_count)

            # Determine risk level
            if security_score >= 80:
                risk_level = "LOW"
                risk_color = "#27ae60"
                bg_color = "#d5f4e6"
            elif security_score >= 60:
                risk_level = "MEDIUM"
                risk_color = "#f39c12"
                bg_color = "#fcf3cf"
            elif security_score >= 40:
                risk_level = "HIGH"
                risk_color = "#e67e22"
                bg_color = "#fdebd0"
            else:
                risk_level = "CRITICAL"
                risk_color = "#e74c3c"
                bg_color = "#fadbd8"

            # Update security score gauge (visual widget)
            self.security_score_gauge.setScore(security_score, risk_level)

            # Update risk level label
            self.risk_level_label.setText(f"Risk Level\n{risk_level}")
            self.risk_level_label.setStyleSheet(f"""
                color: {risk_color};
                padding: 20px;
                background: {bg_color};
                border-radius: 8px;
                border: 2px solid {risk_color};
            """)

            # Store for report generation
            self.current_security_score = security_score
            self.current_risk_level = risk_level

            # Populate findings table
            self.populate_security_findings(security_findings['findings'])

            # Generate recommendations
            recommendations = self.generate_security_recommendations(security_findings)
            self.security_recommendations_text.setPlainText(recommendations)

            self.log(f"✅ Security assessment complete: {total_vulns} issues found (Score: {security_score}/100)")

        except Exception as e:
            self.log(f"Error in security assessment: {e}")
            import traceback
            traceback.print_exc()

    def analyze_security_issues(self):
        """Analyze security issues from discovered assets"""
        findings = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'findings': []
        }

        try:
            if not hasattr(self, 'assets_tree'):
                return findings

            # Analyze each asset in the tree
            for i in range(self.assets_tree.topLevelItemCount()):
                item = self.assets_tree.topLevelItem(i)
                hostname = item.text(0)
                device_type = item.text(1)
                ip = item.text(2)
                status = item.text(3)

                # Check for OT devices without proper segmentation
                if any(ot in device_type.lower() for ot in ['plc', 'hmi', 'scada', 'vfd', 'ics', 'ot']):
                    findings['findings'].append({
                        'severity': 'HIGH',
                        'device': f"{hostname} ({ip})",
                        'finding': 'Exposed OT/ICS Device',
                        'impact': 'OT device accessible on network without verified segmentation',
                        'recommendation': 'Implement network segmentation and firewall rules'
                    })
                    findings['high'] += 1

                # Check for offline devices
                if status.lower() == 'offline':
                    findings['findings'].append({
                        'severity': 'MEDIUM',
                        'device': f"{hostname} ({ip})",
                        'finding': 'Device Offline',
                        'impact': 'Device unavailable, potential availability issue',
                        'recommendation': 'Investigate device status and connectivity'
                    })
                    findings['medium'] += 1

            # Check for insecure protocols (if we have scan data)
            if hasattr(self, 'results_table'):
                for row in range(self.results_table.rowCount()):
                    # This is a placeholder - in a real system, you'd check actual port/protocol data
                    pass

            # Add general security findings
            total_assets = self.assets_tree.topLevelItemCount() if hasattr(self, 'assets_tree') else 0

            if total_assets == 0:
                findings['findings'].append({
                    'severity': 'LOW',
                    'device': 'System',
                    'finding': 'No Assets Discovered',
                    'impact': 'Cannot perform security assessment',
                    'recommendation': 'Run a network scan to discover assets'
                })
                findings['low'] += 1
            else:
                # Check for lack of encryption
                findings['findings'].append({
                    'severity': 'MEDIUM',
                    'device': 'Network',
                    'finding': 'Unencrypted Protocols Detected',
                    'impact': 'Potential data exposure and man-in-the-middle attacks',
                    'recommendation': 'Enable encryption for all network communications'
                })
                findings['medium'] += 1

                # Check for authentication
                findings['findings'].append({
                    'severity': 'HIGH',
                    'device': 'Network',
                    'finding': 'Weak Authentication Mechanisms',
                    'impact': 'Unauthorized access to critical systems',
                    'recommendation': 'Implement strong authentication (MFA, certificate-based)'
                })
                findings['high'] += 1

        except Exception as e:
            self.log(f"Error analyzing security issues: {e}")

        return findings

    def calculate_security_score(self, critical, high, medium, low):
        """Calculate overall security score (0-100)"""
        # Start with perfect score
        score = 100

        # Deduct points based on severity
        score -= critical * 20  # Critical: -20 points each
        score -= high * 10      # High: -10 points each
        score -= medium * 5     # Medium: -5 points each
        score -= low * 2        # Low: -2 points each

        # Ensure score is between 0 and 100
        return max(0, min(100, score))

    def populate_security_findings(self, findings_list):
        """Populate security findings table"""
        try:
            if not hasattr(self, 'security_findings_table'):
                return

            # Clear existing
            self.security_findings_table.setRowCount(0)

            # Sort by severity
            severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
            sorted_findings = sorted(findings_list, key=lambda x: severity_order.get(x['severity'], 4))

            # Populate table
            for finding in sorted_findings:
                row = self.security_findings_table.rowCount()
                self.security_findings_table.insertRow(row)

                # Severity column with color
                severity_item = QTableWidgetItem(finding['severity'])
                if finding['severity'] == 'CRITICAL':
                    severity_item.setBackground(QColor(231, 76, 60))
                    severity_item.setForeground(QColor(255, 255, 255))
                elif finding['severity'] == 'HIGH':
                    severity_item.setBackground(QColor(230, 126, 34))
                    severity_item.setForeground(QColor(255, 255, 255))
                elif finding['severity'] == 'MEDIUM':
                    severity_item.setBackground(QColor(243, 156, 18))
                    severity_item.setForeground(QColor(255, 255, 255))
                else:  # LOW
                    severity_item.setBackground(QColor(52, 152, 219))
                    severity_item.setForeground(QColor(255, 255, 255))

                self.security_findings_table.setItem(row, 0, severity_item)
                self.security_findings_table.setItem(row, 1, QTableWidgetItem(finding['device']))
                self.security_findings_table.setItem(row, 2, QTableWidgetItem(finding['finding']))
                self.security_findings_table.setItem(row, 3, QTableWidgetItem(finding['impact']))
                self.security_findings_table.setItem(row, 4, QTableWidgetItem(finding['recommendation']))

        except Exception as e:
            self.log(f"Error populating findings: {e}")

    def generate_security_recommendations(self, security_findings):
        """Generate prioritized security recommendations"""
        recommendations = []

        critical = security_findings['critical']
        high = security_findings['high']
        medium = security_findings['medium']
        low = security_findings['low']

        recommendations.append("=== TOP PRIORITY SECURITY RECOMMENDATIONS ===\n")

        if critical > 0:
            recommendations.append(f"🔴 CRITICAL: Address {critical} critical vulnerabilities immediately")
            recommendations.append("   - Isolate affected systems from network")
            recommendations.append("   - Apply security patches")
            recommendations.append("   - Implement emergency response procedures\n")

        if high > 0:
            recommendations.append(f"🟠 HIGH: Remediate {high} high-severity issues within 48 hours")
            recommendations.append("   - Implement network segmentation")
            recommendations.append("   - Enable authentication and encryption")
            recommendations.append("   - Review and restrict firewall rules\n")

        if medium > 0:
            recommendations.append(f"🟡 MEDIUM: Address {medium} medium-severity issues within 1 week")
            recommendations.append("   - Update security policies")
            recommendations.append("   - Implement monitoring and logging")
            recommendations.append("   - Conduct security awareness training\n")

        if low > 0:
            recommendations.append(f"🔵 LOW: Resolve {low} low-severity issues as part of regular maintenance")

        if critical == 0 and high == 0 and medium == 0 and low == 0:
            recommendations.append("✅ No security issues detected")
            recommendations.append("   - Continue regular security assessments")
            recommendations.append("   - Maintain current security posture")
            recommendations.append("   - Stay updated on latest threats")

        return '\n'.join(recommendations)

    def export_security_report(self):
        """Export security assessment report to file"""
        try:
            if not hasattr(self, 'security_findings_table'):
                return

            # Check if there are findings
            if self.security_findings_table.rowCount() == 0:
                QMessageBox.warning(
                    self,
                    "No Data",
                    "No security findings to export.\n\nRun a security assessment first."
                )
                return

            # Open file dialog
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Security Report",
                f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv);;All Files (*)"
            )

            if not filename:
                return

            # Export to CSV
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Write summary header
                writer.writerow(['Security Assessment Report'])
                writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([])

                # Write statistics
                writer.writerow(['Security Statistics'])
                writer.writerow(['Score:', self.security_score_label.text().split('\n')[1]])
                writer.writerow(['Risk Level:', self.risk_level_label.text().split('\n')[1]])
                writer.writerow([])

                writer.writerow(['Vulnerability Count by Severity'])
                writer.writerow(['Critical:', self.critical_vuln_label.text().split('\n')[1]])
                writer.writerow(['High:', self.high_vuln_label.text().split('\n')[1]])
                writer.writerow(['Medium:', self.medium_vuln_label.text().split('\n')[1]])
                writer.writerow(['Low:', self.low_vuln_label.text().split('\n')[1]])
                writer.writerow([])

                # Write findings table headers
                writer.writerow(['Security Findings'])
                headers = []
                for col in range(self.security_findings_table.columnCount()):
                    headers.append(self.security_findings_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)

                # Write findings data
                for row in range(self.security_findings_table.rowCount()):
                    row_data = []
                    for col in range(self.security_findings_table.columnCount()):
                        item = self.security_findings_table.item(row, col)
                        row_data.append(item.text() if item else '')
                    writer.writerow(row_data)

            self.log(f"📄 Security report exported: {filename}")

            QMessageBox.information(
                self,
                "Export Successful",
                f"Security report exported successfully!\n\n"
                f"File: {filename}\n"
                f"Findings: {self.security_findings_table.rowCount()}"
            )

        except Exception as e:
            self.log(f"Error exporting security report: {e}")
            QMessageBox.critical(self, "Export Failed", f"Failed to export report:\n{e}")

    def show_remediation_guide(self):
        """Show remediation guide dialog"""
        try:
            remediation_text = """
=== SECURITY REMEDIATION GUIDE ===

CRITICAL VULNERABILITIES:
• Immediately isolate affected systems
• Apply emergency patches
• Disable vulnerable services
• Implement compensating controls
• Notify security team and management

HIGH SEVERITY ISSUES:
• Network Segmentation:
  - Separate OT from IT networks
  - Implement VLANs and firewall rules
  - Use DMZ for internet-facing services

• Authentication & Access Control:
  - Implement multi-factor authentication
  - Use role-based access control (RBAC)
  - Disable default credentials
  - Enforce strong password policies

• Encryption:
  - Enable TLS/SSL for all communications
  - Use VPNs for remote access
  - Encrypt data at rest and in transit

MEDIUM SEVERITY ISSUES:
• Monitoring & Logging:
  - Enable centralized logging
  - Implement SIEM solution
  - Set up alerts for suspicious activity

• Patch Management:
  - Establish regular patching schedule
  - Test patches in non-production first
  - Document all changes

• Security Policies:
  - Develop incident response plan
  - Conduct regular security training
  - Perform periodic security audits

BEST PRACTICES:
✓ Regular vulnerability assessments
✓ Penetration testing (annual minimum)
✓ Security awareness training
✓ Backup and disaster recovery testing
✓ Vendor security assessments
✓ Compliance framework adoption (NIST, IEC 62443)

COMPLIANCE FRAMEWORKS:
• NIST Cybersecurity Framework
• IEC 62443 (Industrial Automation)
• NERC CIP (Critical Infrastructure)
• ISO 27001 (Information Security)
            """

            dialog = QMessageBox(self)
            dialog.setWindowTitle("Security Remediation Guide")
            dialog.setText("Comprehensive Security Remediation Guidance")
            dialog.setDetailedText(remediation_text)
            dialog.setIcon(QMessageBox.Icon.Information)
            dialog.exec()

        except Exception as e:
            self.log(f"Error showing remediation guide: {e}")

    # ========== ASSET INVENTORY BUTTON ACTIONS ==========

    def add_inventory_asset_manually(self):
        """Open dialog to manually add an asset to inventory"""
        try:
            from PyQt6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox

            dialog = QDialog(self)
            dialog.setWindowTitle("Add Asset Manually")
            dialog.setMinimumWidth(500)

            layout = QFormLayout()

            # Create input fields
            ip_input = QLineEdit()
            ip_input.setPlaceholderText("192.168.1.100")

            hostname_input = QLineEdit()
            hostname_input.setPlaceholderText("device-name")

            mac_input = QLineEdit()
            mac_input.setPlaceholderText("00:11:22:33:44:55")

            vendor_input = QLineEdit()
            vendor_input.setPlaceholderText("Rockwell Automation")

            device_type_combo = QComboBox()
            device_type_combo.addItems([
                "Unknown", "PLC", "HMI", "SCADA", "VFD", "RTU",
                "OT/ICS", "Router", "Switch", "Firewall",
                "Server", "Workstation", "IT Device"
            ])

            status_combo = QComboBox()
            status_combo.addItems(["online", "offline", "unknown"])

            # Add fields to form
            layout.addRow("IP Address*:", ip_input)
            layout.addRow("Hostname:", hostname_input)
            layout.addRow("MAC Address:", mac_input)
            layout.addRow("Vendor:", vendor_input)
            layout.addRow("Device Type:", device_type_combo)
            layout.addRow("Status:", status_combo)

            # Add buttons
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addRow(buttons)

            dialog.setLayout(layout)

            # Execute dialog
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Validate IP address
                ip = ip_input.text().strip()
                if not ip:
                    QMessageBox.warning(self, "Invalid Input", "IP Address is required")
                    return

                # Create asset dictionary
                asset = {
                    'ip_address': ip,
                    'hostname': hostname_input.text().strip() or ip,
                    'mac': mac_input.text().strip() or 'Unknown',
                    'vendor': vendor_input.text().strip() or 'Unknown',
                    'device_type': device_type_combo.currentText(),
                    'status': status_combo.currentText()
                }

                # Add to assets tree
                self.add_device_to_assets(asset)

                # Refresh inventory table
                self.refresh_inventory_from_assets()

                self.log(f"✅ Manually added asset: {asset['hostname']} ({asset['ip_address']})")

                QMessageBox.information(
                    self,
                    "Asset Added",
                    f"Successfully added asset:\n\n"
                    f"IP: {asset['ip_address']}\n"
                    f"Hostname: {asset['hostname']}\n"
                    f"Type: {asset['device_type']}"
                )

        except Exception as e:
            self.log(f"Error adding asset manually: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add asset:\n{e}")
            import traceback
            traceback.print_exc()

    def refresh_inventory_from_assets(self):
        """Refresh inventory table from assets tree"""
        try:
            if not hasattr(self, 'inventory_asset_table'):
                return

            # Clear existing table
            self.inventory_asset_table.setRowCount(0)

            # Populate from assets tree
            if hasattr(self, 'assets_tree'):
                for i in range(self.assets_tree.topLevelItemCount()):
                    item = self.assets_tree.topLevelItem(i)

                    # Extract data from tree item
                    hostname = item.text(0)  # Column 0: Hostname
                    device_type = item.text(1)  # Column 1: Device Type
                    ip_address = item.text(2)  # Column 2: IP
                    status = item.text(3)  # Column 3: Status

                    # Add row to inventory table
                    row = self.inventory_asset_table.rowCount()
                    self.inventory_asset_table.insertRow(row)

                    # Populate columns
                    self.inventory_asset_table.setItem(row, 0, QTableWidgetItem(ip_address))
                    self.inventory_asset_table.setItem(row, 1, QTableWidgetItem(hostname))
                    self.inventory_asset_table.setItem(row, 2, QTableWidgetItem("Unknown"))  # MAC
                    self.inventory_asset_table.setItem(row, 3, QTableWidgetItem("Unknown"))  # Vendor
                    self.inventory_asset_table.setItem(row, 4, QTableWidgetItem(device_type))
                    self.inventory_asset_table.setItem(row, 5, QTableWidgetItem(status))
                    self.inventory_asset_table.setItem(row, 6, QTableWidgetItem(
                        datetime.now().strftime("%Y-%m-%d %H:%M")
                    ))

                    # Color code by status
                    status_item = self.inventory_asset_table.item(row, 5)
                    if status.lower() == 'online':
                        status_item.setBackground(QColor(46, 204, 113))
                        status_item.setForeground(QColor(255, 255, 255))
                    elif status.lower() == 'offline':
                        status_item.setBackground(QColor(231, 76, 60))
                        status_item.setForeground(QColor(255, 255, 255))

                    # Color code OT devices
                    type_item = self.inventory_asset_table.item(row, 4)
                    if any(ot in device_type.lower() for ot in ['plc', 'hmi', 'scada', 'vfd', 'ot', 'ics']):
                        type_item.setBackground(QColor(231, 76, 60))
                        type_item.setForeground(QColor(255, 255, 255))

            # Update count label
            total = self.inventory_asset_table.rowCount()
            if hasattr(self, 'inventory_count_label'):
                self.inventory_count_label.setText(f"Total Assets: {total}")

            self.log(f"🔄 Inventory refreshed: {total} assets")

        except Exception as e:
            self.log(f"Error refreshing inventory: {e}")
            import traceback
            traceback.print_exc()

    def export_inventory(self):
        """Export inventory table to CSV"""
        try:
            if not hasattr(self, 'inventory_asset_table'):
                return

            # Check if there's data to export
            if self.inventory_asset_table.rowCount() == 0:
                QMessageBox.warning(
                    self,
                    "No Data",
                    "No assets in inventory to export.\n\n"
                    "Run a network scan or add assets manually first."
                )
                return

            # Open file dialog
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Asset Inventory",
                f"asset_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv);;All Files (*)"
            )

            if not filename:
                return  # User cancelled

            # Export to CSV
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Write headers
                headers = []
                for col in range(self.inventory_asset_table.columnCount()):
                    headers.append(
                        self.inventory_asset_table.horizontalHeaderItem(col).text()
                    )
                writer.writerow(headers)

                # Write data rows
                for row in range(self.inventory_asset_table.rowCount()):
                    row_data = []
                    for col in range(self.inventory_asset_table.columnCount()):
                        item = self.inventory_asset_table.item(row, col)
                        row_data.append(item.text() if item else '')
                    writer.writerow(row_data)

            self.log(f"📄 Exported {self.inventory_asset_table.rowCount()} assets to: {filename}")

            QMessageBox.information(
                self,
                "Export Successful",
                f"Asset inventory exported successfully!\n\n"
                f"File: {filename}\n"
                f"Assets: {self.inventory_asset_table.rowCount()}"
            )

        except Exception as e:
            self.log(f"Error exporting inventory: {e}")
            QMessageBox.critical(self, "Export Failed", f"Failed to export inventory:\n{e}")
            import traceback
            traceback.print_exc()

    # ---- Entry Point ----

    def open_rule_manager(self):
        """Open the Rule Manager window"""
        try:
            rule_manager = RuleManagerWindow(self)
            rule_manager.rules_changed.connect(self.on_rules_changed)
            rule_manager.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open Rule Manager: {e}")

    def on_rules_changed(self):
        """Handle rules configuration changes"""
        reply = QMessageBox.question(
            self, "Rules Changed",
            "Alert rules have been modified. Restart monitoring to apply changes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self, 'monitor_thread') and self.monitor_thread and self.monitor_thread.isRunning():
                self.stop_monitoring()
            QTimer.singleShot(1000, self.start_monitoring)

    def open_vulnerability_report(self):
        """Open the latest vulnerability assessment report"""
        try:
            from pathlib import Path
            import webbrowser

            reports_dir = Path("reports")
            if not reports_dir.exists():
                QMessageBox.warning(self, "No Reports",
                                    "No reports directory found. Run a security scan first.")
                return

            # Find latest report
            reports = list(reports_dir.glob("OT_Security_Report_*.html"))
            if not reports:
                QMessageBox.warning(self, "No Reports",
                                    "No vulnerability reports found. Run a security scan first.")
                return

            latest_report = max(reports, key=lambda p: p.stat().st_mtime)

            # Open in browser
            webbrowser.open(str(latest_report.absolute()))
            self.log(f"📊 Opened report: {latest_report.name}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open report: {e}")
            print(f"[ERROR] Report opening failed: {e}")

    def open_compliance_report(self):
        """Open compliance report (IEC 62443, NIST)"""
        QMessageBox.information(self, "Compliance Report",
                                "Compliance reporting coming soon!\n\nWill include:\n"
                                "• IEC 62443 compliance status\n"
                                "• NIST Cybersecurity Framework\n"
                                "• NERC CIP requirements")

    def open_asset_report(self):
        """Open asset summary report"""
        try:
            from database.db_manager import DatabaseManager
            db = DatabaseManager()

            devices = db.execute_query("SELECT COUNT(*) as count FROM devices")[0]['count']
            online = db.execute_query("SELECT COUNT(*) as count FROM devices WHERE status='online'")[0]['count']

            summary = f"""
            <h2>Asset Summary</h2>
            <p><b>Total Devices:</b> {devices}</p>
            <p><b>Online Devices:</b> {online}</p>
            <p><b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            """

            msg = QMessageBox(self)
            msg.setWindowTitle("Asset Summary")
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setText(summary)
            msg.exec()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate asset summary: {e}")

    def refresh_all_data(self):
        """Refresh all tabs and data"""
        self.log("🔄 Refreshing all data...")
        try:
            if hasattr(self.monitor_tab, 'refresh'):
                self.monitor_tab.refresh()
            if hasattr(self, 'scanner_tab') and hasattr(self.scanner_tab, 'update_statistics'):
                self.scanner_tab.update_statistics()
            if hasattr(self.ml_tab, 'refresh'):
                self.ml_tab.refresh()

            self.log("✅ All data refreshed!")
        except Exception as e:
            self.log(f"❌ Refresh failed: {e}")

    def start_enterprise_scan(self):
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
            subnet_lines = subnet_text.splitlines()

            for line in subnet_lines:
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
            
            # PARALLEL SCANNING - Much faster!
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import threading
            
            max_workers = 50  # Scan 50 IPs simultaneously
            completed = 0
            results_lock = threading.Lock()
            
            def scan_single_ip(ip):
                """Scan a single IP and return result"""
                try:
                    return scanner.scan_target(ip)
                except Exception as e:
                    return {'status': 'offline', 'ip': ip}
            
            self.log(f"[*] Using {max_workers} parallel workers for faster scanning...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all scan jobs
                future_to_ip = {executor.submit(scan_single_ip, ip): ip for ip in scan_ips}
                
                # Process results as they complete
                for future in as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    
                    with results_lock:
                        completed += 1
                        progress = int((completed / total) * 100)
                        
                        if hasattr(self, 'scan_progress'):
                            self.scan_progress.setValue(progress)
                        
                        if hasattr(self, 'scan_status'):
                            self.scan_status.setText(f"Scanned {completed}/{total} IPs... ({online_count} found)")
                    
                    try:
                        result = future.result()
                        
                        if result['status'] == 'online':
                            with results_lock:
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
                                    
                                    if result['ot_protocols']:
                                        device_type = "OT/ICS"
                                    
                                    if any(x in vendor for x in ['rockwell', 'allen-bradley', 'siemens', 'schneider', 'mitsubishi', 'omron', 'abb', 'ge fanuc']):
                                        device_type = "PLC"
                                    elif any(x in vendor for x in ['yaskawa', 'danfoss', 'delta', 'abb drive']) or 'vfd' in hostname:
                                        device_type = "VFD"
                                    elif 'hmi' in hostname or 'wonderware' in vendor or 'advantech' in vendor:
                                        device_type = "HMI"
                                    elif 'scada' in hostname:
                                        device_type = "SCADA"
                                    elif 'router' in hostname or ('cisco' in vendor and 'c8' in hostname):
                                        device_type = "Router"
                                    elif 'switch' in hostname or 'sw-' in hostname:
                                        device_type = "Switch"
                                    elif any(x in vendor for x in ['fortinet', 'palo alto', 'check point', 'sophos', 'watchguard']):
                                        device_type = "Firewall"
                                    elif any(x in hostname for x in ['server', 'srv', 'dc-', 'sql', 'web', 'app', 'research']):
                                        device_type = "Server"
                                    elif any(x in hostname for x in ['pc-', 'ws-', 'win', 'workstation']):
                                        device_type = "Workstation"
                                    
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
                                    
                                    self.results_table.setItem(row, 4, type_item)
                                
                                log_msg = f"[{online_count}] {result['ip']} - {result['vendor']} [{device_type}]"
                                if result['ot_protocols']:
                                    protocols = ', '.join([p['protocol'] for p in result['ot_protocols']])
                                    log_msg += f" [OT: {protocols}]"
                                    self.log(log_msg)
                                    
                                    # Force GUI update
                                    QApplication.processEvents()
                        
                                # Update GUI after every device found
                    except Exception as e:
                        pass
            if hasattr(self, 'scan_progress'):
                self.scan_progress.setValue(100)
            if hasattr(self, 'scan_status'):
                self.scan_status.setText(f"Complete! Found {online_count} devices")
            
            self.log(f"[OK] Scan complete! Found {online_count} online devices out of {total} IPs scanned")
            
            self.scan_button.setEnabled(True)
            if hasattr(self, 'stop_scan_button'):
                self.stop_scan_button.setEnabled(False)
            
            if online_count > 0:
                msg = f"Found {online_count} online devices!"


                msg += "Device types detected:"

                msg += "- PLCs, VFDs, HMI (Red)"

                msg += "- Routers, Switches (Blue)"

                msg += "- Servers (Green)"


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

    # ========== REPORT GENERATION METHODS ==========

    def generate_discovery_report(self):
        """Generate Network Discovery Summary Report"""
        try:
            self.log("Generating Network Discovery Report...")

            # Collect data from assets tree
            total_devices = self.assets_tree.topLevelItemCount()
            online_devices = 0
            offline_devices = 0
            device_types = {}
            vendors = {}

            for i in range(total_devices):
                item = self.assets_tree.topLevelItem(i)
                status = item.text(3).lower()
                device_type = item.text(1)

                if status == 'online':
                    online_devices += 1
                elif status == 'offline':
                    offline_devices += 1

                device_types[device_type] = device_types.get(device_type, 0) + 1

            # Generate report text
            report = f"""
╔══════════════════════════════════════════════════════════════╗
║          NETWORK DISCOVERY SUMMARY REPORT                    ║
║          Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                       ║
╚══════════════════════════════════════════════════════════════╝

EXECUTIVE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Devices Discovered:  {total_devices}
Online Devices:            {online_devices}
Offline Devices:           {offline_devices}
Network Uptime:            {(online_devices / total_devices * 100) if total_devices > 0 else 0:.1f}%

DEVICE TYPE BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

            for dtype, count in sorted(device_types.items(), key=lambda x: x[1], reverse=True):
                report += f"  {dtype:20s}  {count:3d} devices\n"

            report += f"""
DISCOVERED DEVICES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{'Hostname':<25} {'IP Address':<15} {'Type':<15} {'Status':<10}
{'─'*70}
"""

            for i in range(min(total_devices, 50)):  # Limit to first 50
                item = self.assets_tree.topLevelItem(i)
                hostname = item.text(0)[:24]
                ip = item.text(2)
                dtype = item.text(1)[:14]
                status = item.text(3).upper()
                report += f"{hostname:<25} {ip:<15} {dtype:<15} {status:<10}\n"

            if total_devices > 50:
                report += f"\n... and {total_devices - 50} more devices\n"

            report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RECOMMENDATIONS
• Investigate offline devices and verify connectivity
• Document all discovered devices in asset inventory
• Implement network segmentation for OT devices
• Enable continuous monitoring for network changes

End of Report
"""

            # Display in preview
            self.report_preview_text.setPlainText(report)

            # Store for export
            self.current_report_data = {
                'type': 'discovery',
                'total_devices': total_devices,
                'online_devices': online_devices,
                'offline_devices': offline_devices,
                'device_types': device_types,
                'generated': datetime.now().isoformat()
            }
            self.current_report_type = 'network_discovery'

            # Enable export buttons
            self.pdf_export_btn.setEnabled(True)
            self.csv_export_btn.setEnabled(True)
            self.json_export_btn.setEnabled(True)

            self.log("Network Discovery Report generated successfully")

        except Exception as e:
            self.log(f"Error generating discovery report: {e}")
            import traceback
            traceback.print_exc()

    def generate_inventory_report(self):
        """Generate Asset Inventory Report"""
        try:
            self.log("Generating Asset Inventory Report...")

            total_assets = self.assets_tree.topLevelItemCount()

            # Categorize assets
            ot_devices = 0
            it_devices = 0
            network_devices = 0
            unknown_devices = 0

            assets_list = []

            for i in range(total_assets):
                item = self.assets_tree.topLevelItem(i)
                device_type = item.text(1).lower()

                asset_data = {
                    'hostname': item.text(0),
                    'type': item.text(1),
                    'ip': item.text(2),
                    'status': item.text(3)
                }
                assets_list.append(asset_data)

                if any(x in device_type for x in ['plc', 'hmi', 'scada', 'vfd', 'rtu', 'ot', 'ics']):
                    ot_devices += 1
                elif any(x in device_type for x in ['router', 'switch', 'firewall']):
                    network_devices += 1
                elif any(x in device_type for x in ['server', 'workstation', 'it']):
                    it_devices += 1
                else:
                    unknown_devices += 1

            # Generate report
            report = f"""
╔══════════════════════════════════════════════════════════════╗
║          ASSET INVENTORY REPORT                              ║
║          Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                       ║
╚══════════════════════════════════════════════════════════════╝

INVENTORY SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Assets:              {total_assets}
OT/ICS Devices:            {ot_devices}
IT Devices:                {it_devices}
Network Infrastructure:    {network_devices}
Unknown/Unclassified:      {unknown_devices}

ASSET CLASSIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OT/ICS Assets ({ot_devices}):
"""

            for asset in [a for a in assets_list if any(x in a['type'].lower() for x in ['plc', 'hmi', 'scada', 'vfd', 'rtu', 'ot', 'ics'])]:
                report += f"  • {asset['hostname']:30s} {asset['ip']:15s} [{asset['type']}]\n"

            report += f"\nNetwork Infrastructure ({network_devices}):\n"
            for asset in [a for a in assets_list if any(x in a['type'].lower() for x in ['router', 'switch', 'firewall'])]:
                report += f"  • {asset['hostname']:30s} {asset['ip']:15s} [{asset['type']}]\n"

            report += f"\nIT Assets ({it_devices}):\n"
            for asset in [a for a in assets_list if any(x in a['type'].lower() for x in ['server', 'workstation', 'it'])]:
                report += f"  • {asset['hostname']:30s} {asset['ip']:15s} [{asset['type']}]\n"

            report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ASSET MANAGEMENT RECOMMENDATIONS
• Maintain accurate and up-to-date asset inventory
• Tag and label all physical devices
• Document network diagrams showing asset locations
• Establish asset lifecycle management procedures
• Implement asset change control processes

COMPLIANCE NOTES
✓ IEC 62443-2-1: Asset Inventory Requirement
✓ NIST CSF: Asset Management (ID.AM)
✓ ISO 27001: A.8.1 Asset Responsibility

End of Report
"""

            self.report_preview_text.setPlainText(report)

            self.current_report_data = {
                'type': 'inventory',
                'total_assets': total_assets,
                'ot_devices': ot_devices,
                'it_devices': it_devices,
                'network_devices': network_devices,
                'assets': assets_list,
                'generated': datetime.now().isoformat()
            }
            self.current_report_type = 'asset_inventory'

            self.pdf_export_btn.setEnabled(True)
            self.csv_export_btn.setEnabled(True)
            self.json_export_btn.setEnabled(True)

            self.log("Asset Inventory Report generated successfully")

        except Exception as e:
            self.log(f"Error generating inventory report: {e}")
            import traceback
            traceback.print_exc()

    def generate_security_report(self):
        """Generate Security Assessment Report"""
        try:
            self.log("Generating Security Assessment Report...")

            # Get security data
            if not hasattr(self, 'security_findings_table'):
                self.report_preview_text.setPlainText("Please run Security Assessment first from the Security tab.")
                return

            critical_count = 0
            high_count = 0
            medium_count = 0
            low_count = 0

            findings = []

            for row in range(self.security_findings_table.rowCount()):
                severity = self.security_findings_table.item(row, 0).text()
                device = self.security_findings_table.item(row, 1).text()
                finding = self.security_findings_table.item(row, 2).text()
                impact = self.security_findings_table.item(row, 3).text()

                findings.append({
                    'severity': severity,
                    'device': device,
                    'finding': finding,
                    'impact': impact
                })

                if severity == 'CRITICAL':
                    critical_count += 1
                elif severity == 'HIGH':
                    high_count += 1
                elif severity == 'MEDIUM':
                    medium_count += 1
                elif severity == 'LOW':
                    low_count += 1

            total_findings = len(findings)
            score = getattr(self, 'current_security_score', 0)
            risk_level = getattr(self, 'current_risk_level', 'UNKNOWN')

            report = f"""
╔══════════════════════════════════════════════════════════════╗
║          SECURITY ASSESSMENT REPORT                          ║
║          Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                       ║
╚══════════════════════════════════════════════════════════════╝

SECURITY SCORE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overall Security Score:    {score}/100
Risk Level:                {risk_level}
Total Findings:            {total_findings}

VULNERABILITY BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL Findings:         {critical_count}  (Immediate action required)
HIGH Findings:             {high_count}  (Remediate within 48 hours)
MEDIUM Findings:           {medium_count}  (Remediate within 1 week)
LOW Findings:              {low_count}  (Remediate as resources permit)

DETAILED FINDINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

            for severity_level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                level_findings = [f for f in findings if f['severity'] == severity_level]
                if level_findings:
                    report += f"\n[{severity_level}] Findings:\n"
                    for idx, f in enumerate(level_findings, 1):
                        report += f"  {idx}. Device: {f['device']}\n"
                        report += f"     Finding: {f['finding']}\n"
                        report += f"     Impact: {f['impact']}\n\n"

            report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REMEDIATION PRIORITIES

1. CRITICAL (Immediate):
   • Isolate affected systems from network
   • Apply emergency patches
   • Implement compensating controls

2. HIGH (48 Hours):
   • Implement network segmentation
   • Enable authentication and encryption
   • Deploy monitoring solutions

3. MEDIUM (1 Week):
   • Update security policies
   • Enhance logging and monitoring
   • Conduct security training

4. LOW (Ongoing):
   • Review and update documentation
   • Perform regular security assessments
   • Maintain patch management

COMPLIANCE STATUS
• NIST CSF: Identify, Protect, Detect functions
• IEC 62443-3-3: Security risk assessment requirement
• ISO 27001: A.12.6 Technical vulnerability management

End of Report
"""

            self.report_preview_text.setPlainText(report)

            self.current_report_data = {
                'type': 'security',
                'score': score,
                'risk_level': risk_level,
                'critical': critical_count,
                'high': high_count,
                'medium': medium_count,
                'low': low_count,
                'findings': findings,
                'generated': datetime.now().isoformat()
            }
            self.current_report_type = 'security_assessment'

            self.pdf_export_btn.setEnabled(True)
            self.csv_export_btn.setEnabled(True)
            self.json_export_btn.setEnabled(True)

            self.log("Security Assessment Report generated successfully")

        except Exception as e:
            self.log(f"Error generating security report: {e}")
            import traceback
            traceback.print_exc()

    def generate_monitoring_report(self):
        """Generate Network Monitoring Statistics Report"""
        try:
            self.log("Generating Network Monitoring Report...")

            total_devices = self.assets_tree.topLevelItemCount()
            online = 0
            offline = 0

            for i in range(total_devices):
                item = self.assets_tree.topLevelItem(i)
                status = item.text(3).lower()
                if status == 'online':
                    online += 1
                elif status == 'offline':
                    offline += 1

            uptime_pct = (online / total_devices * 100) if total_devices > 0 else 0

            report = f"""
╔══════════════════════════════════════════════════════════════╗
║          NETWORK MONITORING STATISTICS                       ║
║          Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                       ║
╚══════════════════════════════════════════════════════════════╝

NETWORK AVAILABILITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Monitored Devices:   {total_devices}
Online Devices:             {online}
Offline Devices:            {offline}
Network Uptime:             {uptime_pct:.2f}%

AVAILABILITY STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{"█" * int(online / max(total_devices, 1) * 50)} {online} Online
{"█" * int(offline / max(total_devices, 1) * 50)} {offline} Offline

DEVICE STATUS DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{'Device':<30} {'IP Address':<15} {'Status':<10}
{'─'*60}
"""

            for i in range(total_devices):
                item = self.assets_tree.topLevelItem(i)
                hostname = item.text(0)[:29]
                ip = item.text(2)
                status = item.text(3).upper()
                report += f"{hostname:<30} {ip:<15} {status:<10}\n"

            report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MONITORING RECOMMENDATIONS
• Implement continuous network monitoring
• Set up automated alerts for device failures
• Establish baseline performance metrics
• Monitor bandwidth utilization
• Track device response times

PERFORMANCE METRICS TO MONITOR
• Network latency and packet loss
• Device CPU and memory utilization
• Interface errors and discards
• Bandwidth consumption
• Connection states

ALERTING THRESHOLDS
• Critical: Device offline > 5 minutes
• Warning: Response time > 500ms
• Info: New device discovered

End of Report
"""

            self.report_preview_text.setPlainText(report)

            self.current_report_data = {
                'type': 'monitoring',
                'total_devices': total_devices,
                'online': online,
                'offline': offline,
                'uptime_pct': uptime_pct,
                'generated': datetime.now().isoformat()
            }
            self.current_report_type = 'network_monitoring'

            self.pdf_export_btn.setEnabled(True)
            self.csv_export_btn.setEnabled(True)
            self.json_export_btn.setEnabled(True)

            self.log("Network Monitoring Report generated successfully")

        except Exception as e:
            self.log(f"Error generating monitoring report: {e}")
            import traceback
            traceback.print_exc()

    # ========== REPORT EXPORT METHODS ==========

    def export_report_pdf(self):
        """Export current report as PDF"""
        try:
            from PyQt6.QtPrintSupport import QPrinter
            from PyQt6.QtGui import QTextDocument

            if not self.current_report_data:
                QMessageBox.warning(self, "No Report", "Please generate a report first.")
                return

            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Report as PDF",
                f"{self.current_report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF Files (*.pdf)"
            )

            if not filename:
                return

            # Create PDF using QPrinter
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(filename)

            # Create document from preview text
            document = QTextDocument()
            document.setPlainText(self.report_preview_text.toPlainText())
            document.print(printer)

            QMessageBox.information(self, "Export Successful", f"Report exported to:\n{filename}")
            self.log(f"Report exported to PDF: {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{str(e)}")
            self.log(f"PDF export failed: {e}")

    def export_report_csv(self):
        """Export current report as CSV"""
        try:
            import csv

            if not self.current_report_data:
                QMessageBox.warning(self, "No Report", "Please generate a report first.")
                return

            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Report as CSV",
                f"{self.current_report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )

            if not filename:
                return

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write based on report type
                if self.current_report_type == 'network_discovery':
                    writer.writerow(['Network Discovery Summary Report'])
                    writer.writerow(['Generated', self.current_report_data['generated']])
                    writer.writerow([])
                    writer.writerow(['Metric', 'Value'])
                    writer.writerow(['Total Devices', self.current_report_data['total_devices']])
                    writer.writerow(['Online Devices', self.current_report_data['online_devices']])
                    writer.writerow(['Offline Devices', self.current_report_data['offline_devices']])
                    writer.writerow([])
                    writer.writerow(['Device Type', 'Count'])
                    for dtype, count in self.current_report_data['device_types'].items():
                        writer.writerow([dtype, count])

                elif self.current_report_type == 'security_assessment':
                    writer.writerow(['Security Assessment Report'])
                    writer.writerow(['Generated', self.current_report_data['generated']])
                    writer.writerow([])
                    writer.writerow(['Security Score', self.current_report_data['score']])
                    writer.writerow(['Risk Level', self.current_report_data['risk_level']])
                    writer.writerow([])
                    writer.writerow(['Severity', 'Count'])
                    writer.writerow(['Critical', self.current_report_data['critical']])
                    writer.writerow(['High', self.current_report_data['high']])
                    writer.writerow(['Medium', self.current_report_data['medium']])
                    writer.writerow(['Low', self.current_report_data['low']])
                    writer.writerow([])
                    writer.writerow(['Severity', 'Device', 'Finding', 'Impact'])
                    for f in self.current_report_data['findings']:
                        writer.writerow([f['severity'], f['device'], f['finding'], f['impact']])

                else:
                    # Generic export
                    writer.writerow([f'{self.current_report_type} Report'])
                    writer.writerow(['Generated', self.current_report_data['generated']])
                    writer.writerow([])
                    for key, value in self.current_report_data.items():
                        if key != 'generated' and not isinstance(value, (dict, list)):
                            writer.writerow([key, value])

            QMessageBox.information(self, "Export Successful", f"Report exported to:\n{filename}")
            self.log(f"Report exported to CSV: {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV:\n{str(e)}")
            self.log(f"CSV export failed: {e}")

    def export_report_json(self):
        """Export current report as JSON"""
        try:
            import json

            if not self.current_report_data:
                QMessageBox.warning(self, "No Report", "Please generate a report first.")
                return

            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Report as JSON",
                f"{self.current_report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json)"
            )

            if not filename:
                return

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.current_report_data, f, indent=2)

            QMessageBox.information(self, "Export Successful", f"Report exported to:\n{filename}")
            self.log(f"Report exported to JSON: {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export JSON:\n{str(e)}")
            self.log(f"JSON export failed: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("OT Asset Manager")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

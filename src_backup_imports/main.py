#!/usr/bin/env python3
"""
OT Asset Manager - Main Application Entry Point
Industrial Asset Discovery and Management System
"""

import sys
import logging
import ctypes
import os
from pathlib import Path

from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QMessageBox

# Add src to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


# Set up logging
def setup_logging():
    """Configure logging with Windows-compatible encoding"""
    os.makedirs('logs', exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/ot_asset_manager.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return os.getuid() == 0  # Unix/Linux

if not is_admin():
    print("⚠️ Scanner requires administrator privileges!")
    print("Please restart the application as administrator.")
def setup_application():
    """Configure the QApplication with proper settings"""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt

    app = QApplication(sys.argv)
    app.setApplicationName("OT Asset Manager")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Industrial Security Solutions")

    # PyQt6 high DPI handling
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass

    return app


def start_enterprise_scan(self):
    """Start multi-subnet network scan with proper error handling"""

    # Validate input
    subnet_text = self.subnet_input.toPlainText().strip()
    if not subnet_text:
        QMessageBox.warning(self, "No Subnets", "Please enter at least one subnet to scan")
        return

    subnets = [line.strip() for line in subnet_text.split('\n') if line.strip()]

    # Validate subnets
    valid_subnets = []
    for subnet in subnets:
        try:
            ipaddress.ip_network(subnet, strict=False)
            valid_subnets.append(subnet)
        except ValueError:
            self.log(f"⚠️ Invalid subnet format: {subnet}")

    if not valid_subnets:
        QMessageBox.warning(self, "Invalid Subnets", "No valid subnets to scan")
        return

    self.log(f"🚀 Starting scan of {len(valid_subnets)} subnets...")
    self.log(f"   Subnets: {', '.join(valid_subnets)}")

    # Check dependencies
    try:
        import nmap
        import scapy.all
        self.log("✅ Network scanning libraries available")
    except ImportError as e:
        self.log(f"❌ Missing dependency: {e}")
        QMessageBox.critical(
            self,
            "Missing Dependencies",
            "Network scanning requires:\n"
            "- python-nmap\n"
            "- scapy\n"
            "- npcap (Windows)\n\n"
            "Install with: pip install python-nmap scapy"
        )
        return

    # Check permissions
    if not self.check_admin_privileges():
        reply = QMessageBox.question(
            self,
            "Administrator Required",
            "Network scanning requires administrator privileges.\n"
            "Current scan will run in limited mode.\n\n"
            "Continue anyway?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

    # Initialize scanner
    try:
        from scanner.network_scanner import EnterpriseNetworkScanner
        self.scanner = EnterpriseNetworkScanner(max_workers=self.max_workers.value())
        self.log("✅ Scanner initialized successfully")
    except Exception as e:
        self.log(f"❌ Scanner initialization failed: {e}")
        QMessageBox.critical(self, "Scanner Error", f"Failed to initialize scanner:\n{e}")
        return

    # Show progress
    self.scan_progress.setVisible(True)
    self.scan_progress.setRange(0, 0)  # Indeterminate
    self.scan_button.setEnabled(False)
    self.stop_button.setEnabled(True)

    # Run scan in background
    self.scan_thread = QThread()
    self.scan_worker = ScanWorker(self.scanner, valid_subnets)
    self.scan_worker.moveToThread(self.scan_thread)

    self.scan_thread.started.connect(self.scan_worker.run)
    self.scan_worker.finished.connect(self.on_scan_complete)
    self.scan_worker.progress.connect(self.log)
    self.scan_worker.error.connect(self.on_scan_error)

    self.scan_thread.start()


def check_admin_privileges(self):
    """Check if running with admin/root privileges"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        import os
        return os.getuid() == 0


def on_scan_error(self, error_msg):
    """Handle scan errors"""
    self.log(f"❌ Scan error: {error_msg}")
    self.scan_progress.setVisible(False)
    self.scan_button.setEnabled(True)
    self.stop_button.setEnabled(False)

    QMessageBox.critical(self, "Scan Failed", f"Network scan failed:\n{error_msg}")


def create_test_window():
    """Create a test window if main window fails"""
    from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QMessageBox
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont

    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("OT Asset Manager - Test Mode")
            self.setGeometry(300, 300, 800, 600)

            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 16px;
                    padding: 20px;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 15px 32px;
                    text-align: center;
                    font-size: 16px;
                    margin: 4px 2px;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)

            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)

            title = QLabel("OT Asset Manager")
            title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)

            status = QLabel(
                "Import Error - Using Test Mode\n\n"
                "The main window couldn't be imported.\n"
                "This usually means there's an import issue in main_window.py\n\n"
                "Check the console output for specific error details."
            )
            status.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(status)

            btn_close = QPushButton("Close Application")
            btn_close.clicked.connect(self.close)
            layout.addWidget(btn_close)

        def show_test_dialog(self):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("GUI Test")
            msg.setText("PyQt6 GUI components working!")
            msg.exec()

    return TestWindow()


def main():
    """Main application entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting OT Asset Manager...")

        # Setup Qt Application
        app = setup_application()

        # Try to import and create main window
        try:
            logger.info("Importing main window...")
            from gui.main_window import MainWindow

            logger.info("Creating main window...")
            window = MainWindow()
            window.show()
            logger.info("Main window created successfully")

        except ImportError as e:
            logger.error(f"Failed to import MainWindow: {e}")
            logger.info("Creating test window instead...")
            window = create_test_window()
            window.show()
            logger.info("Test window created")

        except Exception as e:
            logger.error(f"Failed to create MainWindow: {e}")
            logger.info("Creating test window instead...")
            window = create_test_window()
            window.show()
            logger.info("Test window created")

        logger.info("Application ready - starting event loop")
        return app.exec()

    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

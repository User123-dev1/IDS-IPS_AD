"""
Rule Manager Window - GUI for managing custom alert rules
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QDialog, QFormLayout,
    QLineEdit, QComboBox, QSpinBox, QTextEdit, QCheckBox, QLabel,
    QMessageBox, QHeaderView, QGroupBox, QListWidget, QListWidgetItem,
    QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon


class RuleEditorDialog(QDialog):
    """Dialog for creating/editing alert rules"""
    
    def __init__(self, parent=None, rule_data: Optional[Dict] = None):
        super().__init__(parent)
        self.rule_data = rule_data or {}
        self.is_editing = bool(rule_data)
        
        self.setWindowTitle("Edit Rule" if self.is_editing else "New Rule")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        
        if self.is_editing:
            self.load_rule_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Rule ID
        self.id_input = QLineEdit()
        if self.is_editing:
            self.id_input.setReadOnly(True)
            self.id_input.setText(self.rule_data.get('id', ''))
        else:
            self.id_input.setPlaceholderText("e.g., rule_010")
        form_layout.addRow("Rule ID:", self.id_input)
        
        # Rule Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., SSH Access Monitoring")
        form_layout.addRow("Name:", self.name_input)
        
        # Description
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Describe what this rule detects...")
        self.desc_input.setMaximumHeight(80)
        form_layout.addRow("Description:", self.desc_input)
        
        # Enabled
        self.enabled_check = QCheckBox("Rule Enabled")
        self.enabled_check.setChecked(True)
        form_layout.addRow("Status:", self.enabled_check)
        
        # Severity
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.severity_combo.setCurrentText("MEDIUM")
        form_layout.addRow("Severity:", self.severity_combo)
        
        # Category
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("e.g., SSH_ACCESS")
        form_layout.addRow("Category:", self.category_input)
        
        layout.addLayout(form_layout)
        
        # Conditions Group
        conditions_group = QGroupBox("Rule Conditions")
        conditions_layout = QVBoxLayout()
        
        condition_form = QFormLayout()
        
        # Condition Type
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "port",
            "connection_rate",
            "packet_rate",
            "dns_queries",
            "ip_blacklist"
        ])
        self.type_combo.currentTextChanged.connect(self.on_condition_type_changed)
        condition_form.addRow("Type:", self.type_combo)
        
        # Operator
        self.operator_combo = QComboBox()
        self.operator_combo.addItems(["in", "not_in", "greater_than", "less_than"])
        condition_form.addRow("Operator:", self.operator_combo)
        
        # Values (for port, ip_blacklist)
        self.values_input = QLineEdit()
        self.values_input.setPlaceholderText("e.g., 22,23,3389 or 192.168.1.100,10.0.0.50")
        self.values_label = QLabel("Values (comma-separated):")
        condition_form.addRow(self.values_label, self.values_input)
        
        # Threshold value (for rate-based rules)
        self.value_input = QSpinBox()
        self.value_input.setRange(1, 10000)
        self.value_input.setValue(20)
        self.value_label = QLabel("Threshold:")
        condition_form.addRow(self.value_label, self.value_input)
        
        # Timeframe (for rate-based rules)
        self.timeframe_input = QSpinBox()
        self.timeframe_input.setRange(10, 3600)
        self.timeframe_input.setValue(60)
        self.timeframe_input.setSuffix(" seconds")
        self.timeframe_label = QLabel("Timeframe:")
        condition_form.addRow(self.timeframe_label, self.timeframe_input)
        
        conditions_layout.addLayout(condition_form)
        conditions_group.setLayout(conditions_layout)
        layout.addWidget(conditions_group)
        
        # Update visibility based on initial type
        self.on_condition_type_changed(self.type_combo.currentText())
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Rule")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; padding: 8px; font-weight: bold; }")
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("QPushButton { background-color: #6c757d; color: white; padding: 8px; }")
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def on_condition_type_changed(self, condition_type: str):
        """Update form fields based on condition type"""
        if condition_type in ["port", "ip_blacklist"]:
            # Show values field, hide threshold and timeframe
            self.values_label.show()
            self.values_input.show()
            self.value_label.hide()
            self.value_input.hide()
            self.timeframe_label.hide()
            self.timeframe_input.hide()
            
            # Update operator options
            self.operator_combo.clear()
            self.operator_combo.addItems(["in", "not_in"])
            
        else:  # rate-based rules
            # Hide values, show threshold and timeframe
            self.values_label.hide()
            self.values_input.hide()
            self.value_label.show()
            self.value_input.show()
            self.timeframe_label.show()
            self.timeframe_input.show()
            
            # Update operator options
            self.operator_combo.clear()
            self.operator_combo.addItems(["greater_than", "less_than"])
    
    def load_rule_data(self):
        """Load existing rule data into form"""
        self.name_input.setText(self.rule_data.get('name', ''))
        self.desc_input.setPlainText(self.rule_data.get('description', ''))
        self.enabled_check.setChecked(self.rule_data.get('enabled', True))
        self.severity_combo.setCurrentText(self.rule_data.get('severity', 'MEDIUM'))
        self.category_input.setText(self.rule_data.get('category', ''))
        
        conditions = self.rule_data.get('conditions', {})
        cond_type = conditions.get('type', 'port')
        self.type_combo.setCurrentText(cond_type)
        self.operator_combo.setCurrentText(conditions.get('operator', 'in'))
        
        if 'values' in conditions:
            values = conditions['values']
            if isinstance(values, list):
                self.values_input.setText(','.join(map(str, values)))
        
        if 'value' in conditions:
            self.value_input.setValue(conditions['value'])
        
        if 'timeframe' in conditions:
            self.timeframe_input.setValue(conditions['timeframe'])
    
    def get_rule_data(self) -> Dict:
        """Get rule data from form"""
        rule = {
            'id': self.id_input.text().strip(),
            'name': self.name_input.text().strip(),
            'description': self.desc_input.toPlainText().strip(),
            'enabled': self.enabled_check.isChecked(),
            'severity': self.severity_combo.currentText(),
            'category': self.category_input.text().strip().upper().replace(' ', '_'),
            'conditions': {
                'type': self.type_combo.currentText(),
                'operator': self.operator_combo.currentText()
            }
        }
        
        # Add condition-specific fields
        cond_type = self.type_combo.currentText()
        
        if cond_type in ["port", "ip_blacklist"]:
            values_text = self.values_input.text().strip()
            if values_text:
                if cond_type == "port":
                    rule['conditions']['values'] = [int(v.strip()) for v in values_text.split(',') if v.strip().isdigit()]
                else:  # ip_blacklist
                    rule['conditions']['values'] = [v.strip() for v in values_text.split(',') if v.strip()]
            else:
                rule['conditions']['values'] = []
        else:  # rate-based
            rule['conditions']['value'] = self.value_input.value()
            rule['conditions']['timeframe'] = self.timeframe_input.value()
        
        return rule


class WhitelistManager(QWidget):
    """Widget for managing IP and port whitelists"""
    
    whitelist_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Use absolute path based on script location
        script_dir = Path(__file__).resolve().parent  # gui folder
        project_root = script_dir.parent.parent  # project root
        self.config_path = project_root / "config" / "alert_rules.json"
        
        # Debug: print path
        print(f"[Rule Manager] Config path: {self.config_path}")
        print(f"[Rule Manager] Config exists: {self.config_path.exists()}")
        self.setup_ui()
        self.load_whitelists()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Splitter for IP and Port whitelists
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # IP Whitelist
        ip_group = QGroupBox("IP Whitelist")
        ip_layout = QVBoxLayout()
        
        ip_label = QLabel("Trusted IP addresses that won't trigger alerts:")
        ip_label.setWordWrap(True)
        ip_layout.addWidget(ip_label)
        
        self.ip_list = QListWidget()
        ip_layout.addWidget(self.ip_list)
        
        ip_button_layout = QHBoxLayout()
        add_ip_btn = QPushButton("Add IP")
        add_ip_btn.clicked.connect(self.add_ip)
        remove_ip_btn = QPushButton("Remove")
        remove_ip_btn.clicked.connect(self.remove_ip)
        ip_button_layout.addWidget(add_ip_btn)
        ip_button_layout.addWidget(remove_ip_btn)
        ip_layout.addLayout(ip_button_layout)
        
        ip_group.setLayout(ip_layout)
        splitter.addWidget(ip_group)
        
        # Port Whitelist
        port_group = QGroupBox("Port Whitelist")
        port_layout = QVBoxLayout()
        
        port_label = QLabel("Ports that are considered normal/trusted:")
        port_label.setWordWrap(True)
        port_layout.addWidget(port_label)
        
        self.port_list = QListWidget()
        port_layout.addWidget(self.port_list)
        
        port_button_layout = QHBoxLayout()
        add_port_btn = QPushButton("Add Port")
        add_port_btn.clicked.connect(self.add_port)
        remove_port_btn = QPushButton("Remove")
        remove_port_btn.clicked.connect(self.remove_port)
        port_button_layout.addWidget(add_port_btn)
        port_button_layout.addWidget(remove_port_btn)
        port_layout.addLayout(port_button_layout)
        
        port_group.setLayout(port_layout)
        splitter.addWidget(port_group)
        
        layout.addWidget(splitter)
        
        # Save button
        save_btn = QPushButton("Save Whitelist Changes")
        save_btn.clicked.connect(self.save_whitelists)
        save_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; padding: 10px; font-weight: bold; }")
        layout.addWidget(save_btn)
    
    def load_whitelists(self):
        """Load whitelist from config"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8-sig') as f:
                    config = json.load(f)
                
                whitelist = config.get('whitelist', {})
                
                # Load IPs
                self.ip_list.clear()
                for ip in whitelist.get('ips', []):
                    self.ip_list.addItem(ip)
                
                # Load Ports
                self.port_list.clear()
                for port in whitelist.get('ports', []):
                    self.port_list.addItem(str(port))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load whitelist: {e}")
    
    def save_whitelists(self):
        """Save whitelist to config"""
        try:
            # Load current config
            with open(self.config_path, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
            
            # Update whitelist
            whitelist = {
                'ips': [self.ip_list.item(i).text() for i in range(self.ip_list.count())],
                'ports': [int(self.port_list.item(i).text()) for i in range(self.port_list.count())]
            }
            
            config['whitelist'] = whitelist
            
            # Save config
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            QMessageBox.information(self, "Success", "Whitelist saved successfully!")
            self.whitelist_changed.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save whitelist: {e}")
    
    def add_ip(self):
        """Add IP to whitelist"""
        from PyQt6.QtWidgets import QInputDialog
        
        ip, ok = QInputDialog.getText(self, "Add IP", "Enter IP address:")
        if ok and ip:
            # Simple validation
            parts = ip.split('.')
            if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                self.ip_list.addItem(ip)
            else:
                QMessageBox.warning(self, "Invalid IP", "Please enter a valid IP address")
    
    def remove_ip(self):
        """Remove selected IP"""
        current = self.ip_list.currentRow()
        if current >= 0:
            self.ip_list.takeItem(current)
    
    def add_port(self):
        """Add port to whitelist"""
        from PyQt6.QtWidgets import QInputDialog
        
        port, ok = QInputDialog.getInt(self, "Add Port", "Enter port number:", 80, 1, 65535)
        if ok:
            self.port_list.addItem(str(port))
    
    def remove_port(self):
        """Remove selected port"""
        current = self.port_list.currentRow()
        if current >= 0:
            self.port_list.takeItem(current)


class RuleManagerWindow(QMainWindow):
    """Main Rule Manager Window"""
    
    rules_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Use absolute path based on script location
        script_dir = Path(__file__).resolve().parent  # gui folder
        project_root = script_dir.parent.parent  # project root
        self.config_path = project_root / "config" / "alert_rules.json"
        
        # Debug: print path
        print(f"[Rule Manager] Config path: {self.config_path}")
        print(f"[Rule Manager] Config exists: {self.config_path.exists()}")
        
        self.setWindowTitle("Alert Rules Manager")
        self.resize(900, 600)
        
        self.setup_ui()
        self.load_rules()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Rules tab
        rules_tab = QWidget()
        rules_layout = QVBoxLayout(rules_tab)
        
        # Rules table
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(6)
        self.rules_table.setHorizontalHeaderLabels([
            "Enabled", "ID", "Name", "Severity", "Category", "Actions"
        ])
        self.rules_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.rules_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.rules_table.setAlternatingRowColors(True)
        
        rules_layout.addWidget(self.rules_table)
        
        # Button bar
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add New Rule")
        add_btn.clicked.connect(self.add_rule)
        add_btn.setStyleSheet("QPushButton { background-color: #007bff; color: white; padding: 8px; font-weight: bold; }")
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_rules)
        
        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self.export_rules)
        
        import_btn = QPushButton("📥 Import")
        import_btn.clicked.connect(self.import_rules)
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(export_btn)
        button_layout.addWidget(import_btn)
        button_layout.addStretch()
        
        rules_layout.addLayout(button_layout)
        
        self.tabs.addTab(rules_tab, "📋 Rules")
        
        # Whitelist tab
        self.whitelist_widget = WhitelistManager()
        self.whitelist_widget.whitelist_changed.connect(self.on_config_changed)
        self.tabs.addTab(self.whitelist_widget, "✅ Whitelist")
        
        layout.addWidget(self.tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def load_rules(self):
        """Load rules from config file"""
        try:
            if not self.config_path.exists():
                QMessageBox.warning(self, "Config Not Found", 
                                   "Alert rules configuration file not found!")
                return
            
            with open(self.config_path, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
            
            rules = config.get('rules', [])
            
            self.rules_table.setRowCount(len(rules))
            
            for row, rule in enumerate(rules):
                # Enabled checkbox
                enabled_widget = QWidget()
                enabled_layout = QHBoxLayout(enabled_widget)
                enabled_layout.setContentsMargins(0, 0, 0, 0)
                enabled_check = QCheckBox()
                enabled_check.setChecked(rule.get('enabled', True))
                enabled_check.stateChanged.connect(lambda state, r=rule['id']: self.toggle_rule(r, state))
                enabled_layout.addWidget(enabled_check)
                enabled_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.rules_table.setCellWidget(row, 0, enabled_widget)
                
                # ID
                self.rules_table.setItem(row, 1, QTableWidgetItem(rule.get('id', '')))
                
                # Name
                self.rules_table.setItem(row, 2, QTableWidgetItem(rule.get('name', '')))
                
                # Severity
                severity_item = QTableWidgetItem(rule.get('severity', ''))
                severity = rule.get('severity', 'MEDIUM')
                if severity == 'CRITICAL':
                    severity_item.setBackground(QColor(220, 53, 69))
                    severity_item.setForeground(QColor(255, 255, 255))
                elif severity == 'HIGH':
                    severity_item.setBackground(QColor(255, 193, 7))
                elif severity == 'MEDIUM':
                    severity_item.setBackground(QColor(255, 235, 59))
                else:  # LOW
                    severity_item.setBackground(QColor(200, 200, 200))
                self.rules_table.setItem(row, 3, severity_item)
                
                # Category
                self.rules_table.setItem(row, 4, QTableWidgetItem(rule.get('category', '')))
                
                # Action buttons
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(4, 4, 4, 4)
                
                edit_btn = QPushButton("✏️ Edit")
                edit_btn.clicked.connect(lambda checked, r=rule: self.edit_rule(r))
                edit_btn.setStyleSheet("QPushButton { padding: 4px 8px; }")
                
                delete_btn = QPushButton("🗑️ Delete")
                delete_btn.clicked.connect(lambda checked, r=rule['id']: self.delete_rule(r))
                delete_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; padding: 4px 8px; }")
                
                action_layout.addWidget(edit_btn)
                action_layout.addWidget(delete_btn)
                
                self.rules_table.setCellWidget(row, 5, action_widget)
            
            self.statusBar().showMessage(f"Loaded {len(rules)} rules", 3000)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load rules: {e}")
    
    def add_rule(self):
        """Open dialog to add new rule"""
        dialog = RuleEditorDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            rule_data = dialog.get_rule_data()
            
            # Validate
            if not rule_data['id'] or not rule_data['name']:
                QMessageBox.warning(self, "Validation Error", "Rule ID and Name are required!")
                return
            
            # Add to config
            try:
                with open(self.config_path, 'r', encoding='utf-8-sig') as f:
                    config = json.load(f)
                
                # Check for duplicate ID
                if any(r['id'] == rule_data['id'] for r in config['rules']):
                    QMessageBox.warning(self, "Duplicate ID", "A rule with this ID already exists!")
                    return
                
                config['rules'].append(rule_data)
                
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                
                self.load_rules()
                self.rules_changed.emit()
                QMessageBox.information(self, "Success", "Rule added successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add rule: {e}")
    
    def edit_rule(self, rule: Dict):
        """Open dialog to edit rule"""
        dialog = RuleEditorDialog(self, rule)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            rule_data = dialog.get_rule_data()
            
            # Update in config
            try:
                with open(self.config_path, 'r', encoding='utf-8-sig') as f:
                    config = json.load(f)
                
                # Find and update rule
                for i, r in enumerate(config['rules']):
                    if r['id'] == rule['id']:
                        config['rules'][i] = rule_data
                        break
                
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                
                self.load_rules()
                self.rules_changed.emit()
                QMessageBox.information(self, "Success", "Rule updated successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not update rule: {e}")
    
    def delete_rule(self, rule_id: str):
        """Delete a rule"""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete rule '{rule_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(self.config_path, 'r', encoding='utf-8-sig') as f:
                    config = json.load(f)
                
                config['rules'] = [r for r in config['rules'] if r['id'] != rule_id]
                
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                
                self.load_rules()
                self.rules_changed.emit()
                QMessageBox.information(self, "Success", "Rule deleted successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete rule: {e}")
    
    def toggle_rule(self, rule_id: str, state: int):
        """Enable/disable a rule"""
        try:
            with open(self.config_path, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
            
            for rule in config['rules']:
                if rule['id'] == rule_id:
                    rule['enabled'] = (state == Qt.CheckState.Checked.value)
                    break
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            self.rules_changed.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not toggle rule: {e}")
    
    def export_rules(self):
        """Export rules to file"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Rules", "", "JSON Files (*.json)"
        )
        
        if filename:
            try:
                import shutil
                shutil.copy(self.config_path, filename)
                QMessageBox.information(self, "Success", "Rules exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not export rules: {e}")
    
    def import_rules(self):
        """Import rules from file"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Rules", "", "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    config = json.load(f)
                
                # Validate structure
                if 'rules' not in config:
                    QMessageBox.warning(self, "Invalid File", "Not a valid rules configuration file!")
                    return
                
                # Backup current config
                backup_path = self.config_path.with_suffix('.json.backup')
                import shutil
                shutil.copy(self.config_path, backup_path)
                
                # Import
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                
                self.load_rules()
                self.rules_changed.emit()
                QMessageBox.information(self, "Success", 
                                       f"Rules imported successfully!\nBackup saved to: {backup_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not import rules: {e}")
    
    def on_config_changed(self):
        """Handle configuration changes"""
        self.rules_changed.emit()


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = RuleManagerWindow()
    window.show()
    sys.exit(app.exec())


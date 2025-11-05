import re

print("[*] Enhancing color coding...")
with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the device type item coloring and enhance it
old_color = r'type_item = QTableWidgetItem\(device_type\)\s+if result\[\'ot_protocols\'\]:\s+type_item\.setBackground\(QColor\(231, 76, 60\)\).*?type_item\.setForeground\(QColor\(255, 255, 255\)\)'

new_color = '''type_item = QTableWidgetItem(device_type)
                            
                            # Color code by device type
                            if device_type in ["PLC", "OT/ICS", "VFD", "HMI", "SCADA"]:
                                type_item.setBackground(QColor(231, 76, 60))  # Red for OT devices
                                type_item.setForeground(QColor(255, 255, 255))
                            elif device_type in ["Router", "Switch", "Firewall"]:
                                type_item.setBackground(QColor(52, 152, 219))  # Blue for network devices
                                type_item.setForeground(QColor(255, 255, 255))
                            elif device_type == "Server":
                                type_item.setBackground(QColor(46, 204, 113))  # Green for servers
                                type_item.setForeground(QColor(255, 255, 255))
                            elif device_type == "Workstation":
                                type_item.setBackground(QColor(149, 165, 166))  # Gray for workstations
                                type_item.setForeground(QColor(255, 255, 255))'''

content = re.sub(old_color, new_color, content, flags=re.DOTALL)

with open("../src/gui/main_window.py", "w", encoding="utf-8") as f:
    f.write(content)

print("[OK] Color coding enhanced!")
print("\n[*] Colors:")
print("    RED: PLCs, VFDs, HMI, SCADA, OT/ICS")
print("    BLUE: Routers, Switches, Firewalls")
print("    GREEN: Servers")
print("    GRAY: Workstations")


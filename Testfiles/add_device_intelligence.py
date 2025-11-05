import re

print("[*] Adding device type intelligence...")
with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the device type assignment and replace with intelligent detection
old_pattern = r'device_type = "OT/ICS" if result\[\'ot_protocols\'\] else "IT"'

new_logic = '''# INTELLIGENT DEVICE TYPE DETECTION
                            device_type = "IT"  # Default
                            
                            # Check for OT/ICS devices first
                            if result['ot_protocols']:
                                device_type = "OT/ICS"
                            
                            # Check vendor-based device types
                            vendor = result['vendor'].lower()
                            hostname = result['hostname'].lower()
                            
                            # PLCs (Programmable Logic Controllers)
                            if any(plc in vendor for plc in ['rockwell', 'allen-bradley', 'siemens', 'schneider', 'mitsubishi', 'omron', 'abb']):
                                device_type = "PLC"
                            
                            # VFDs (Variable Frequency Drives)
                            elif any(vfd in vendor for vfd in ['yaskawa', 'abb drive', 'danfoss', 'delta']) or 'vfd' in hostname:
                                device_type = "VFD"
                            
                            # HMI (Human Machine Interface)
                            elif any(hmi in vendor for hmi in ['wonderware', 'advantech']) or 'hmi' in hostname:
                                device_type = "HMI"
                            
                            # SCADA Systems
                            elif 'scada' in hostname or 'scada' in vendor:
                                device_type = "SCADA"
                            
                            # Routers
                            elif 'cisco' in vendor or 'router' in hostname or 'juniper' in vendor:
                                device_type = "Router"
                            
                            # Switches
                            elif any(sw in hostname for sw in ['switch', 'sw-']) or ('cisco' in vendor and 'catalyst' in hostname):
                                device_type = "Switch"
                            
                            # Firewalls
                            elif any(fw in vendor for fw in ['fortinet', 'palo alto', 'check point', 'sophos', 'watchguard']):
                                device_type = "Firewall"
                            
                            # Servers (based on hostname patterns)
                            elif any(srv in hostname for srv in ['server', 'srv', 'dc-', 'sql', 'web', 'app', 'db']):
                                device_type = "Server"
                            
                            # Windows/Linux hosts
                            elif any(ws in hostname for ws in ['win', 'pc-', 'ws-', 'workstation']):
                                device_type = "Workstation"
                            
                            # IoT devices
                            elif any(iot in vendor for iot in ['raspberry', 'arduino', 'esp']):
                                device_type = "IoT Device"
                            
                            # If still OT/ICS from protocols, keep it
                            if device_type == "IT" and result['ot_protocols']:
                                device_type = "OT/ICS"'''

content = re.sub(old_pattern, new_logic, content, flags=re.DOTALL)

with open("../src/gui/main_window.py", "w", encoding="utf-8") as f:
    f.write(content)

print("[OK] Device type intelligence added!")
print("\n[*] Now detects:")
print("    - PLCs (Rockwell, Siemens, Schneider, etc.)")
print("    - VFDs (Variable Frequency Drives)")
print("    - HMI (Human Machine Interface)")
print("    - Routers (Cisco, Juniper)")
print("    - Switches")
print("    - Firewalls (Check Point, Fortinet, etc.)")
print("    - Servers, Workstations, IoT")


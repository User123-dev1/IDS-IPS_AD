import sys
from pathlib import Path
import requests
import ipaddress
import socket
import struct
import subprocess
import threading
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent / "src"))

from scanner.network_scanner import EnterpriseNetworkScanner

print("=" * 70)
print("  ADVANCED OT/ICS NETWORK SCANNER")
print("  Multi-Method Vendor & Device Detection")
print("=" * 70)

# ============================================================================
# COMPREHENSIVE INDUSTRIAL MAC DATABASE
# ============================================================================

INDUSTRIAL_OUI_DATABASE = {
    # Rockwell Automation / Allen-Bradley (Complete List)
    "00:00:BC": ("Rockwell Automation", "Industrial Controller"),
    "00:15:2B": ("Rockwell Automation", "ControlLogix"),
    "00:1D:9C": ("Rockwell Automation", "CompactLogix"),
    "00:22:B4": ("Rockwell Automation", "Flex I/O"),
    "00:A0:2F": ("Rockwell Automation", "PLC Module"),
    "00:A0:45": ("Rockwell Automation", "Phoenix Contact"),
    "00:A0:83": ("Rockwell Automation", "PowerFlex Drive"),
    "00:C0:8E": ("Rockwell Automation", "Network Module"),
    "00:C0:F2": ("Rockwell Automation", "Legacy PLC"),
    "00:D0:BC": ("Rockwell Automation", "Allen-Bradley PLC"),
    "00:E0:18": ("Rockwell Automation", "RSLinx Gateway"),
    "28:80:A2": ("Rockwell Automation", "Stratix Switch"),
    "30:64:69": ("Rockwell Automation", "PowerFlex VFD"),
    "40:9B:CD": ("Rockwell Automation", "CompactLogix L3"),
    "44:D3:CA": ("Rockwell Automation", "GuardLogix"),
    "5C:88:16": ("Rockwell Automation", "Kinetix Drive"),
    "60:52:D0": ("Rockwell Automation", "PanelView HMI"),
    "6C:F0:49": ("Rockwell Automation", "Ethernet Module"),
    "74:FE:48": ("Rockwell Automation", "ControlLogix L8"),
    "88:5D:90": ("Rockwell Automation", "CompactLogix L2"),
    "94:CC:39": ("Rockwell Automation", "Flex5000 I/O"),
    "A4:93:4C": ("Rockwell Automation", "PowerFlex 525"),
    "B4:B5:2F": ("Rockwell Automation", "CompactLogix L1"),
    "B8:E8:56": ("Rockwell Automation", "PanelView Plus"),
    "C4:93:80": ("Rockwell Automation", "FactoryTalk Server"),
    "DC:0F:18": ("Rockwell Automation", "Stratix 5700"),
    "EC:44:76": ("Rockwell Automation", "CompactLogix 5380"),
    "F4:54:33": ("Rockwell Automation", "PowerFlex 755"),

    # Siemens
    "00:01:02": ("Siemens", "SIMATIC S7-1200"),
    "00:0E:8C": ("Siemens", "SCALANCE Switch"),
    "00:13:95": ("Siemens", "S7-300"),
    "00:15:B7": ("Siemens", "S7-400"),
    "00:1B:1B": ("Siemens", "SIMATIC S7-1500"),
    "00:1F:F8": ("Siemens", "PROFINET Device"),
    "00:50:06": ("Siemens", "HMI Touch Panel"),
    "00:90:93": ("Siemens", "WinCC Server"),
    "08:00:06": ("Siemens", "Industrial PC"),
    "20:87:56": ("Siemens", "S7-1200 V4"),
    "34:2E:B6": ("Siemens", "S7-1500 CPU"),
    "50:02:91": ("Siemens", "ET200SP"),
    "78:2B:CB": ("Siemens", "S7-300 CPU"),
    "88:0B:0D": ("Siemens", "Logo Controller"),
    "A0:36:9F": ("Siemens", "SIMATIC HMI"),
    "C8:E7:D8": ("Siemens", "PROFIBUS Gateway"),
    "F8:BC:12": ("Siemens", "S7-400 CPU"),

    # Schneider Electric / Modicon
    "00:00:54": ("Schneider Electric", "Modicon M580"),
    "00:00:AA": ("Schneider Electric", "Modicon M340"),
    "00:05:5D": ("Schneider Electric", "Industrial Gateway"),
    "00:20:85": ("Schneider Electric", "Premium PLC"),
    "00:40:9F": ("Schneider Electric", "Modicon Quantum"),
    "00:60:16": ("Schneider Electric", "Variable Speed Drive"),
    "00:80:F4": ("Schneider Electric", "Altivar VFD"),
    "00:90:E8": ("Schneider Electric", "ConneXium Switch"),
    "00:C0:37": ("Schneider Electric", "Unity Processor"),
    "28:6E:D4": ("Schneider Electric", "M262 Controller"),
    "40:98:AD": ("Schneider Electric", "Altivar Process"),
    "58:C3:8B": ("Schneider Electric", "TM3 Module"),
    "70:82:0E": ("Schneider Electric", "Magelis HMI"),
    "84:37:62": ("Schneider Electric", "M221 Controller"),
    "B8:27:EB": ("Schneider Electric", "Edge Controller"),

    # ABB
    "00:0A:46": ("ABB", "AC500 PLC"),
    "00:0F:9F": ("ABB", "Freelance Controller"),
    "00:1A:AA": ("ABB", "ACS Drive"),
    "00:30:71": ("ABB", "800xA Controller"),
    "00:50:60": ("ABB", "IRC5 Robot Controller"),
    "00:66:78": ("ABB", "ACS880 VFD"),
    "00:90:3E": ("ABB", "System 800"),
    "10:0B:A9": ("ABB", "AC500 V2"),
    "40:D8:55": ("ABB", "RobotStudio"),
    "68:79:24": ("ABB", "Ability System"),

    # Honeywell
    "00:30:11": ("Honeywell", "C300 Controller"),
    "00:40:84": ("Honeywell", "Experion PKS"),
    "00:50:C2": ("Honeywell", "HC900 Controller"),
    "00:80:A3": ("Honeywell", "Safety Manager"),
    "00:90:7F": ("Honeywell", "ControlEdge"),
    "40:9D:5E": ("Honeywell", "RTU2020"),

    # Mitsubishi
    "00:0A:0E": ("Mitsubishi", "Q Series PLC"),
    "00:0C:7A": ("Mitsubishi", "FX5 PLC"),
    "00:15:17": ("Mitsubishi", "iQ-R Series"),
    "00:1E:35": ("Mitsubishi", "GOT HMI"),
    "00:30:13": ("Mitsubishi", "FR Drive"),
    "00:40:26": ("Mitsubishi", "A Series PLC"),
    "00:80:92": ("Mitsubishi", "L Series PLC"),
    "CC:05:1B": ("Mitsubishi", "iQ-F Series"),

    # Omron
    "00:00:48": ("Omron", "CJ Series PLC"),
    "00:10:E8": ("Omron", "CP Series PLC"),
    "00:20:4A": ("Omron", "CS Series PLC"),
    "00:30:2B": ("Omron", "NJ Controller"),
    "00:40:3F": ("Omron", "NX Controller"),
    "00:80:2D": ("Omron", "Sysmac Studio"),
    "00:90:CC": ("Omron", "NS HMI"),
    "44:A6:E5": ("Omron", "NX701 Controller"),

    # Yokogawa
    "00:00:86": ("Yokogawa", "CENTUM VP"),
    "00:0A:E6": ("Yokogawa", "ProSafe-RS"),
    "00:20:2B": ("Yokogawa", "STARDOM"),
    "00:80:8C": ("Yokogawa", "FA-M3"),
    "00:A0:59": ("Yokogawa", "UT Controller"),

    # Emerson / GE
    "00:0C:0C": ("Emerson", "DeltaV Controller"),
    "00:15:2C": ("Emerson", "Ovation Controller"),
    "00:20:07": ("GE", "RX3i Controller"),
    "00:40:C8": ("GE", "Mark VIe"),
    "00:80:1E": ("GE", "90-30 PLC"),
    "00:90:4B": ("GE", "RX7i Controller"),
    "00:E0:43": ("Emerson", "ROC800"),

    # Other Industrial
    "00:03:7A": ("Toshiba", "nv Series"),
    "00:05:5D": ("D-Link Industrial", "DIS Switch"),
    "00:0B:3B": ("Wago", "750 Series"),
    "00:0F:FE": ("Beckhoff", "TwinCAT PLC"),
    "00:13:49": ("Zyxel", "Industrial Switch"),
    "00:15:BC": ("Moxa", "EDS Switch"),
    "00:1B:54": ("Cisco", "Industrial Ethernet"),
    "00:30:05": ("Fujitsu", "Controller"),
    "00:30:A4": ("Woodhead", "Applicom"),
    "00:40:01": ("Zero One", "Industrial PC"),
    "00:40:8C": ("AXIS", "Video Encoder"),
    "00:50:01": ("Yamaha", "Controller"),
    "00:60:2E": ("Danfoss", "VLT Drive"),
    "00:80:2F": ("National Instruments", "cRIO"),
    "00:90:2B": ("Eaton", "PowerXL Drive"),
    "00:C0:B7": ("American Megatrends", "IPMI"),
    "00:E0:4C": ("Realtek Industrial", "Controller"),
    "08:00:05": ("Symbolics", "Legacy"),
    "08:00:37": ("Fuji Xerox", "Controller"),
    "40:B0:34": ("Weintek", "cMT HMI"),
    "C8:3E:99": ("Texas Instruments", "Sitara")
}

# ============================================================================
# DEVICE FINGERPRINTS AND SIGNATURES
# ============================================================================

DEVICE_FINGERPRINTS = {
    # Rockwell PowerFlex VFDs
    "powerflex_525": {
        "ports": [44818, 80, 2222],
        "services": ["http", "enip"],
        "http_headers": ["PowerFlex", "1756-EN", "Rockwell"],
        "enip_vendor": 0x01
    },
    "powerflex_755": {
        "ports": [44818, 80, 443, 2222],
        "services": ["https", "enip"],
        "http_headers": ["PowerFlex", "20-COMM-E"],
        "enip_vendor": 0x01
    },
    "kinetix_5500": {
        "ports": [44818, 2222, 80],
        "services": ["enip", "http"],
        "http_headers": ["Kinetix", "2198"],
        "enip_vendor": 0x01
    },

    # Rockwell PLCs
    "controllogix_5580": {
        "ports": [44818, 2222, 80, 443],
        "services": ["enip", "https"],
        "http_headers": ["1756-L8", "ControlLogix"],
        "enip_vendor": 0x01,
        "product_codes": [0x0C, 0x0E, 0x10]
    },
    "compactlogix_5380": {
        "ports": [44818, 2222, 80, 443],
        "services": ["enip", "https"],
        "http_headers": ["5069-L3", "CompactLogix"],
        "enip_vendor": 0x01,
        "product_codes": [0x1E, 0x1F, 0x20]
    },

    # Siemens
    "s7_1200": {
        "ports": [102, 80, 443, 502],
        "services": ["s7comm", "http", "modbus"],
        "http_headers": ["S7-1200", "Siemens"]
    },
    "s7_1500": {
        "ports": [102, 80, 443, 502, 161],
        "services": ["s7comm", "https", "snmp"],
        "http_headers": ["S7-1500", "CPU 151"]
    },

    # Schneider
    "m340": {
        "ports": [502, 80, 21, 23, 161],
        "services": ["modbus", "http", "ftp"],
        "modbus_slave_id": range(1, 248)
    },
    "m580": {
        "ports": [502, 80, 443, 44818, 2222, 8080],
        "services": ["modbus", "https", "enip"],
        "http_headers": ["M580", "Schneider"]
    }
}

# ============================================================================
# PROTOCOL DETECTION SIGNATURES
# ============================================================================

PROTOCOL_SIGNATURES = {
    "enip": {
        "ports": [44818, 2222],
        "probe": b"\x65\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00",
        "response_pattern": b"\x65\x00",
        "vendors": {
            0x0001: "Rockwell Automation",
            0x0002: "Schneider Electric",
            0x0018: "Omron",
            0x0032: "Metso",
            0x0037: "SEW Eurodrive"
        }
    },
    "modbus": {
        "ports": [502],
        "probe": b"\x00\x00\x00\x00\x00\x06\x01\x03\x00\x00\x00\x01",
        "response_pattern": b"\x00\x00\x00\x00",
        "function_codes": {
            0x01: "Read Coils",
            0x02: "Read Discrete Inputs",
            0x03: "Read Holding Registers",
            0x04: "Read Input Registers"
        }
    },
    "s7comm": {
        "ports": [102],
        "probe": b"\x03\x00\x00\x16\x11\xe0\x00\x00\x00\x01\x00\xc0\x01\x0a\xc1\x02\x01\x02\xc2\x02\x01\x00",
        "response_pattern": b"\x03\x00",
        "cpu_types": {
            b"6ES7 212": "S7-200",
            b"6ES7 312": "S7-300",
            b"6ES7 412": "S7-400",
            b"6ES7 511": "S7-1200",
            b"6ES7 515": "S7-1500"
        }
    },
    "opcua": {
        "ports": [4840, 4843, 4855],
        "probe": b"OPC",
        "response_pattern": b"opc.tcp"
    },
    "bacnet": {
        "ports": [47808],
        "probe": b"\x81\x0a\x00\x0b\x01\x00\x04\x00\x05\x00",
        "response_pattern": b"\x81"
    },
    "dnp3": {
        "ports": [20000],
        "probe": b"\x05\x64",
        "response_pattern": b"\x05\x64"
    }
}

# ============================================================================
# HTTP BANNER SIGNATURES
# ============================================================================

HTTP_BANNER_SIGNATURES = {
    # Rockwell
    "rockwell_patterns": [
        "PowerFlex", "ControlLogix", "CompactLogix", "Kinetix", "PanelView",
        "1756-", "1769-", "1734-", "1746-", "1747-", "1771-", "1785-",
        "Rockwell Automation", "Allen-Bradley", "A-B", "RSLogix", "FactoryTalk"
    ],

    # Siemens
    "siemens_patterns": [
        "SIMATIC", "S7-200", "S7-300", "S7-400", "S7-1200", "S7-1500",
        "SCALANCE", "WinCC", "TIA Portal", "Siemens AG", "ET 200"
    ],

    # Schneider
    "schneider_patterns": [
        "Modicon", "M340", "M580", "Quantum", "Premium", "Unity",
        "Schneider Electric", "ConneXium", "Altivar", "TM3", "Zelio"
    ],

    # ABB
    "abb_patterns": [
        "AC500", "ACS880", "ACS580", "IRC5", "800xA", "Freelance",
        "ABB Automation", "System 800", "Ability"
    ]
}


# ============================================================================
# ADVANCED DETECTION FUNCTIONS
# ============================================================================

def probe_enip_device(ip, port=44818, timeout=2):
    """Probe EtherNet/IP device for vendor and product info"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))

        # Send List Identity command
        list_identity = b"\x63\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        sock.send(list_identity)

        response = sock.recv(1024)
        sock.close()

        if len(response) > 44:
            # Extract vendor ID (bytes 44-45)
            vendor_id = struct.unpack('<H', response[44:46])[0]

            # Map vendor ID
            vendor_map = {
                0x0001: "Rockwell Automation",
                0x0002: "Schneider Electric",
                0x0018: "Omron",
                0x0032: "Metso",
                0x0037: "SEW Eurodrive",
                0x004D: "Yaskawa",
                0x0056: "Fanuc"
            }

            vendor = vendor_map.get(vendor_id, f"Unknown (ID: {vendor_id})")

            # Try to extract product name
            product_name = ""
            if len(response) > 50:
                try:
                    name_offset = 50
                    name_length = response[name_offset]
                    if name_length > 0 and name_length < 100:
                        product_name = response[name_offset + 1:name_offset + 1 + name_length].decode('utf-8',
                                                                                                      errors='ignore')
                except:
                    pass

            return {
                "vendor": vendor,
                "vendor_id": vendor_id,
                "product": product_name,
                "protocol": "EtherNet/IP"
            }
    except:
        pass

    return None


def probe_modbus_device(ip, port=502, timeout=2):
    """Probe Modbus device for identification"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))

        # Read Device Identification (Function code 43)
        device_id_request = b"\x00\x01\x00\x00\x00\x05\x01\x2b\x0e\x01\x00"
        sock.send(device_id_request)

        response = sock.recv(1024)
        sock.close()

        if len(response) > 8:
            # Parse Modbus response
            if response[7] == 0x2b and response[8] == 0x0e:
                # Device identification response
                vendor = "Modbus Device"

                # Check for specific patterns
                response_str = response.decode('utf-8', errors='ignore')
                if "Schneider" in response_str:
                    vendor = "Schneider Electric"
                elif "Modicon" in response_str:
                    vendor = "Schneider Electric (Modicon)"
                elif "ABB" in response_str:
                    vendor = "ABB"

                return {
                    "vendor": vendor,
                    "protocol": "Modbus TCP"
                }
    except:
        pass

    return None


def probe_http_banners(ip, port=80, timeout=2):
    """Probe HTTP/HTTPS for device identification banners"""
    for port in [80, 443, 8080, 8443]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))

            # Send HTTP GET request
            request = b"GET / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n"
            sock.send(request)

            response = sock.recv(4096).decode('utf-8', errors='ignore')
            sock.close()

            # Check for vendor patterns
            response_lower = response.lower()

            for pattern in HTTP_BANNER_SIGNATURES["rockwell_patterns"]:
                if pattern.lower() in response_lower:
                    return {
                        "vendor": "Rockwell Automation",
                        "pattern": pattern,
                        "port": port
                    }

            for pattern in HTTP_BANNER_SIGNATURES["siemens_patterns"]:
                if pattern.lower() in response_lower:
                    return {
                        "vendor": "Siemens",
                        "pattern": pattern,
                        "port": port
                    }

            for pattern in HTTP_BANNER_SIGNATURES["schneider_patterns"]:
                if pattern.lower() in response_lower:
                    return {
                        "vendor": "Schneider Electric",
                        "pattern": pattern,
                        "port": port
                    }

            for pattern in HTTP_BANNER_SIGNATURES["abb_patterns"]:
                if pattern.lower() in response_lower:
                    return {
                        "vendor": "ABB",
                        "pattern": pattern,
                        "port": port
                    }
        except:
            continue

    return None


def enhanced_mac_lookup(mac):
    """Enhanced MAC address vendor lookup"""
    if not mac or mac == "N/A" or mac == "Unknown":
        return "Unknown", "Unknown Device"

    # Clean MAC
    mac_clean = mac.upper().replace(':', '').replace('-', '').replace('.', '')
    if len(mac_clean) < 6:
        return "Unknown", "Unknown Device"

    # Format MAC prefix
    mac_prefix = ':'.join([mac_clean[i:i + 2] for i in range(0, 6, 2)])

    # Check local database first
    if mac_prefix in INDUSTRIAL_OUI_DATABASE:
        return INDUSTRIAL_OUI_DATABASE[mac_prefix]

    # Check 8-character prefix (some vendors use longer OUI)
    if len(mac_clean) >= 8:
        mac_prefix_long = ':'.join([mac_clean[i:i + 2] for i in range(0, 8, 2)])
        for oui in INDUSTRIAL_OUI_DATABASE:
            if mac_prefix_long.startswith(oui):
                return INDUSTRIAL_OUI_DATABASE[oui]

    # API fallback
    try:
        url = f"https://api.macvendors.co/api/mac/{mac_clean[:6]}"
        response = requests.get(url, timeout=2)
        data = response.json()
        vendor = data.get('result', {}).get('company', 'Unknown')
        return vendor, "Generic Device"
    except:
        pass

    return "Unknown", "Unknown Device"


def classify_device_advanced(device_info):
    """Advanced device classification using all available methods"""
    ip = device_info.get('ip')
    mac = device_info.get('mac_address')
    hostname = device_info.get('hostname', '').lower()
    open_ports = device_info.get('open_ports', [])

    # Extract port numbers
    ports = []
    for port in open_ports:
        if isinstance(port, dict):
            ports.append(port.get('port', 0))
        else:
            ports.append(port)

    vendor = "Unknown"
    device_type = "Unknown Device"
    confidence = 0

    # Method 1: MAC Address Lookup (Highest Priority)
    if mac and mac != "Unknown":
        vendor_info = enhanced_mac_lookup(mac)
        if vendor_info[0] != "Unknown":
            vendor = vendor_info[0]
            device_type = vendor_info[1]
            confidence += 40

    # Method 2: Protocol Probing
    if 44818 in ports or 2222 in ports:
        # EtherNet/IP device
        enip_info = probe_enip_device(ip, 44818 if 44818 in ports else 2222)
        if enip_info:
            vendor = enip_info['vendor']
            if enip_info['product']:
                device_type = enip_info['product']
            else:
                device_type = "EtherNet/IP Device"
            confidence += 50

            # Specific Rockwell device classification
            if "Rockwell" in vendor:
                if "powerflex" in str(enip_info.get('product', '')).lower():
                    device_type = "PowerFlex VFD"
                elif "kinetix" in str(enip_info.get('product', '')).lower():
                    device_type = "Kinetix Servo Drive"
                elif "compact" in str(enip_info.get('product', '')).lower():
                    device_type = "CompactLogix PLC"
                elif "control" in str(enip_info.get('product', '')).lower():
                    device_type = "ControlLogix PLC"
                elif "panelview" in str(enip_info.get('product', '')).lower():
                    device_type = "PanelView HMI"

    elif 502 in ports:
        # Modbus device
        modbus_info = probe_modbus_device(ip)
        if modbus_info:
            vendor = modbus_info['vendor']
            device_type = "Modbus TCP Device"
            confidence += 40

    # Method 3: HTTP Banner Detection
    if 80 in ports or 443 in ports or 8080 in ports:
        http_info = probe_http_banners(ip)
        if http_info:
            if confidence < 50:  # Only override if we're not confident
                vendor = http_info['vendor']
            confidence += 30

            # Refine device type based on banner
            if "PowerFlex" in http_info.get('pattern', ''):
                device_type = "PowerFlex VFD"
            elif "ControlLogix" in http_info.get('pattern', ''):
                device_type = "ControlLogix PLC"
            elif "CompactLogix" in http_info.get('pattern', ''):
                device_type = "CompactLogix PLC"
            elif "PanelView" in http_info.get('pattern', ''):
                device_type = "PanelView HMI"

    # Method 4: Hostname Pattern Matching
    hostname_patterns = {
        "powerflex": ("Rockwell Automation", "PowerFlex VFD"),
        "vfd": ("Industrial", "Variable Frequency Drive"),
        "drive": ("Industrial", "Motor Drive"),
        "plc": ("Industrial", "PLC Controller"),
        "hmi": ("Industrial", "HMI Panel"),
        "compactlogix": ("Rockwell Automation", "CompactLogix PLC"),
        "controllogix": ("Rockwell Automation", "ControlLogix PLC"),
        "simatic": ("Siemens", "SIMATIC Controller"),
        "modicon": ("Schneider Electric", "Modicon PLC"),
        "s7-": ("Siemens", "S7 PLC"),
        "panel": ("Industrial", "HMI Panel")
    }

    for pattern, (h_vendor, h_type) in hostname_patterns.items():
        if pattern in hostname:
            if confidence < 30:  # Only use hostname if we have low confidence
                vendor = h_vendor
                device_type = h_type
            confidence += 20
            break

    # Method 5: Port Signature Matching
    if confidence < 50:
        # Check for specific port combinations
        port_signatures = {
            (44818, 2222, 80): ("Rockwell Automation", "PowerFlex/CompactLogix"),
            (44818, 2222, 443): ("Rockwell Automation", "ControlLogix/GuardLogix"),
            (102, 80, 443): ("Siemens", "S7 PLC"),
            (502, 80, 443): ("Schneider Electric", "Modicon PLC"),
            (502, 80, 161): ("Schneider Electric", "M340/M580"),
            (44818, 80): ("Rockwell Automation", "EtherNet/IP Device"),
            (4840, 80, 443): ("Industrial", "OPC-UA Server"),
            (47808,): ("Industrial", "BACnet Device"),
            (20000,): ("Industrial", "DNP3 Device")
        }

        for port_combo, (p_vendor, p_type) in port_signatures.items():
            if all(p in ports for p in port_combo):
                if vendor == "Unknown":
                    vendor = p_vendor
                    device_type = p_type
                confidence += 25
                break

    # Final classification refinement
    if vendor != "Unknown" and device_type == "Unknown Device":
        # Assign generic device type based on vendor
        vendor_device_map = {
            "Rockwell Automation": "Rockwell Industrial Device",
            "Siemens": "Siemens Industrial Device",
            "Schneider Electric": "Schneider Industrial Device",
            "ABB": "ABB Industrial Device",
            "Honeywell": "Honeywell Controller",
            "Mitsubishi": "Mitsubishi PLC",
            "Omron": "Omron Controller"
        }
        device_type = vendor_device_map.get(vendor, "Industrial Device")

    return {
        "vendor": vendor,
        "device_type": device_type,
        "confidence": confidence,
        "detection_methods": []  # Can be expanded to show which methods were used
    }


# ============================================================================
# MAIN SCANNING FUNCTIONS
# ============================================================================

def get_local_network():
    """Auto-detect local network range"""
    try:
        import netifaces
        gateways = netifaces.gateways()
        default_iface = gateways['default'][netifaces.AF_INET][1]
        addrs = netifaces.ifaddresses(default_iface)
        ip_info = addrs[netifaces.AF_INET][0]
        ip = ip_info['addr']
        netmask = ip_info['netmask']
        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
        return str(network), ip
    except:
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            network_base = '.'.join(local_ip.split('.')[:-1]) + '.0/24'
            return network_base, local_ip
        except:
            return "192.168.12.0/24", "192.168.12.1"


def quick_ping(ip, timeout=1):
    """Quick ping check"""
    try:
        if sys.platform.startswith('win'):
            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
        else:
            cmd = ["ping", "-c", "1", "-W", str(timeout), ip]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout + 1)
        return result.returncode == 0
    except:
        return False


def discover_live_hosts(network_range, max_workers=50):
    """Discover live hosts in network"""
    print(f"\n[*] Discovering live hosts in {network_range}...")

    network = ipaddress.IPv4Network(network_range)
    all_ips = [str(ip) for ip in network.hosts()]

    live_hosts = []
    discovery_lock = threading.Lock()

    def check_host(ip):
        if quick_ping(ip):
            with discovery_lock:
                live_hosts.append(ip)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(check_host, ip) for ip in all_ips]
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 25 == 0:
                print(f"    Progress: {completed}/{len(all_ips)} hosts checked...")

    return sorted(live_hosts, key=lambda x: ipaddress.IPv4Address(x))


def scan_host_comprehensive(scanner, ip):
    """Comprehensive host scanning with multi-method detection"""
    try:
        # Get basic scan results
        result = scanner.scan_target(ip)

        # Apply advanced classification
        classification = classify_device_advanced(result)

        # Update device info
        result['vendor'] = classification['vendor']
        result['device_type'] = classification['device_type']
        result['confidence_score'] = classification['confidence']
        result['scan_success'] = True

        return result

    except Exception as e:
        return {
            'ip': ip,
            'error': str(e),
            'scan_success': False
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

print("\n[*] Initializing advanced detection systems...")
print("    ✓ MAC vendor database loaded: {} entries".format(len(INDUSTRIAL_OUI_DATABASE)))
print("    ✓ Device fingerprints loaded: {} profiles".format(len(DEVICE_FINGERPRINTS)))
print("    ✓ Protocol signatures loaded: {} protocols".format(len(PROTOCOL_SIGNATURES)))
print("    ✓ HTTP banner patterns loaded")

# Initialize scanner
scanner = EnterpriseNetworkScanner()

# Auto-detect network
network_range, local_ip = get_local_network()
print(f"\n[*] Network Configuration:")
print(f"    Network: {network_range}")
print(f"    Local IP: {local_ip}")

# Discover live hosts
live_hosts = discover_live_hosts(network_range)

if not live_hosts:
    print("\n[!] No live hosts found in network!")
    sys.exit(1)

print(f"\n[+] Found {len(live_hosts)} live hosts")
print("[*] Starting comprehensive OT/ICS device identification...")

# Storage for results
all_results = []
device_statistics = defaultdict(int)
vendor_statistics = defaultdict(int)

# Scan all live hosts
print(f"\n{'=' * 90}")
print(f"  COMPREHENSIVE DEVICE IDENTIFICATION")
print(f"{'=' * 90}")

for idx, ip in enumerate(live_hosts, 1):
    print(f"\n[{idx}/{len(live_hosts)}] Analyzing: {ip}")
    print("-" * 60)

    result = scan_host_comprehensive(scanner, ip)
    all_results.append(result)

    if result.get('scan_success'):
        vendor = result.get('vendor', 'Unknown')
        device_type = result.get('device_type', 'Unknown')
        confidence = result.get('confidence_score', 0)
        hostname = result.get('hostname', 'N/A')
        mac = result.get('mac_address', 'N/A')

        # Display results
        print(f"  ├─ Hostname: {hostname}")
        print(f"  ├─ MAC Address: {mac}")
        print(f"  ├─ Vendor: {vendor}")
        print(f"  ├─ Device Type: {device_type}")
        print(f"  ├─ Confidence: {confidence}%")

        # Update statistics
        device_statistics[device_type] += 1
        vendor_statistics[vendor] += 1

        # Show open ports
        ports = result.get('open_ports', [])
        if ports:
            port_list = []
            for p in ports[:8]:
                if isinstance(p, dict):
                    port_num = p.get('port', 'unknown')
                    service = p.get('service', '')
                    port_list.append(f"{port_num}({service})" if service else str(port_num))
                else:
                    port_list.append(str(p))
            print(f"  └─ Ports: {', '.join(port_list)}")
            if len(ports) > 8:
                print(f"     (+{len(ports) - 8} more)")

        # Highlight important findings
        if "Rockwell" in vendor:
            print(f"  🏭 [ROCKWELL DEVICE DETECTED]")
        if "VFD" in device_type or "Drive" in device_type:
            print(f"  ⚡ [VARIABLE FREQUENCY DRIVE]")
        if "PLC" in device_type or "Controller" in device_type:
            print(f"  🎛️ [INDUSTRIAL CONTROLLER]")
        if "HMI" in device_type:
            print(f"  📟 [HUMAN MACHINE INTERFACE]")

    else:
        print(f"  └─ [ERROR] {result.get('error', 'Scan failed')}")

# ============================================================================
# COMPREHENSIVE SUMMARY
# ============================================================================

print(f"\n{'=' * 90}")
print(f"  NETWORK ASSET INVENTORY SUMMARY")
print(f"{'=' * 90}")

# Overall statistics
successful_scans = sum(1 for r in all_results if r.get('scan_success'))
print(f"\n📊 Scan Statistics:")
print(f"    Total hosts scanned: {len(live_hosts)}")
print(f"    Successful identifications: {successful_scans}")
print(f"    Failed scans: {len(live_hosts) - successful_scans}")

# Vendor breakdown
if vendor_statistics:
    print(f"\n🏭 Vendor Distribution:")
    for vendor, count in sorted(vendor_statistics.items(), key=lambda x: x[1], reverse=True):
        if vendor != "Unknown":
            percentage = (count / successful_scans) * 100
            print(f"    {vendor:<30} {count:3} devices ({percentage:.1f}%)")

# Device type breakdown
if device_statistics:
    print(f"\n🔧 Device Type Distribution:")
    for device_type, count in sorted(device_statistics.items(), key=lambda x: x[1], reverse=True):
        if device_type != "Unknown Device":
            percentage = (count / successful_scans) * 100
            print(f"    {device_type:<30} {count:3} devices ({percentage:.1f}%)")

# Rockwell specific summary
rockwell_devices = [r for r in all_results if "Rockwell" in r.get('vendor', '')]
if rockwell_devices:
    print(f"\n⭐ ROCKWELL AUTOMATION DEVICES ({len(rockwell_devices)} found):")
    print("    " + "=" * 60)
    for device in rockwell_devices:
        ip = device.get('ip')
        hostname = device.get('hostname', 'N/A')
        device_type = device.get('device_type', 'Unknown')
        mac = device.get('mac_address', 'N/A')
        print(f"    {ip:<16} {hostname:<25} {device_type}")
        print(f"    {'':16} MAC: {mac}")
        print()

# Critical findings
vfds = [r for r in all_results if "VFD" in r.get('device_type', '') or "Drive" in r.get('device_type', '')]
plcs = [r for r in all_results if "PLC" in r.get('device_type', '') or "Controller" in r.get('device_type', '')]
hmis = [r for r in all_results if "HMI" in r.get('device_type', '') or "Panel" in r.get('device_type', '')]

if vfds or plcs or hmis:
    print(f"\n🎯 Critical OT Assets:")
    if vfds:
        print(f"    Variable Frequency Drives: {len(vfds)}")
    if plcs:
        print(f"    PLCs/Controllers: {len(plcs)}")
    if hmis:
        print(f"    HMI/Panels: {len(hmis)}")

# Export results
try:
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ot_asset_inventory_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\n💾 Results exported to: {filename}")
except Exception as e:
    print(f"\n[!] Could not export results: {e}")

print(f"\n{'=' * 90}")
print("✅ Advanced OT/ICS Asset Discovery Complete!")
print(f"{'=' * 90}\n")

import sys
from pathlib import Path
import socket
import struct
import ipaddress
import subprocess
import platform
from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp
from scapy.config import conf
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

print("=" * 70)
print("  OT/ICS NETWORK ASSET DISCOVERY")
print("  (Industrial Protocols & Live Devices Only)")
print("=" * 70)

# Suppress Scapy warnings
conf.verb = 0

# OT/ICS Protocol Port Definitions
OT_PROTOCOLS = {
    # Modbus
    502: "Modbus TCP",

    # Ethernet/IP & CIP
    44818: "Ethernet/IP",
    2222: "EtherNet/IP I/O",

    # Profinet
    34962: "PROFINET RT",
    34963: "PROFINET RT",
    34964: "PROFINET RT",

    # OPC-UA
    4840: "OPC-UA",
    48020: "OPC-UA Discovery",

    # DNP3
    20000: "DNP3",
    19999: "DNP3 Secure",

    # IEC 61850
    102: "IEC 61850 MMS",
    8102: "IEC 61850",

    # BACnet
    47808: "BACnet",

    # Siemens S7
    102: "Siemens S7",
    1200: "Siemens S7-1200",

    # Schneider Electric
    502: "Schneider Modbus",
    1740: "Schneider",

    # Rockwell/Allen-Bradley
    44818: "EtherNet/IP (AB)",
    2222: "Allen-Bradley",
    9600: "Rockwell FactoryTalk",

    # GE/Emerson
    18245: "GE SRTP",
    18246: "GE SRTP",

    # Honeywell
    1962: "Honeywell",
    4911: "Honeywell",

    # Yokogawa
    10001: "Yokogawa",
    34962: "Yokogawa PROFINET",

    # Common Industrial Services
    21: "FTP (File Transfer)",
    22: "SSH (Secure Shell)",
    23: "Telnet",
    80: "HTTP (Web Interface)",
    443: "HTTPS (Secure Web)",
    161: "SNMP",
    8080: "HTTP Alt (Web Config)",
    8443: "HTTPS Alt",
    3389: "RDP (Remote Desktop)",
    5900: "VNC (Remote Access)",

    # Historian/SCADA
    135: "RPC/DCOM",
    1433: "SQL Server",
    1521: "Oracle DB",
    3306: "MySQL",
    5432: "PostgreSQL"
}

# Group ports by priority for OT environments
CRITICAL_OT_PORTS = [502, 44818, 102, 4840, 20000, 47808]  # Core industrial protocols
COMMON_OT_PORTS = [22, 23, 80, 443, 161, 8080, 8443]  # Management/config
EXTENDED_OT_PORTS = [21, 135, 1433, 1521, 3306, 5432, 3389, 5900, 2222, 1200, 1740, 1962, 4911, 10001, 18245, 18246,
                     9600, 34962, 34963, 34964, 8102, 48020, 19999]

ALL_OT_PORTS = CRITICAL_OT_PORTS + COMMON_OT_PORTS + EXTENDED_OT_PORTS


def get_local_network():
    """Detect local network range"""
    try:
        import netifaces

        gateways = netifaces.gateways()
        default_iface = gateways['default'][netifaces.AF_INET][1]

        addrs = netifaces.ifaddresses(default_iface)
        ip_info = addrs[netifaces.AF_INET][0]

        ip = ip_info['addr']
        netmask = ip_info['netmask']

        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)

        return str(network), default_iface
    except:
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            network_base = '.'.join(local_ip.split('.')[:-1]) + '.0/24'
            return network_base, 'unknown'
        except:
            return "192.168.12.0/24", 'unknown'


def ot_arp_scan(network_range, timeout=3):
    """ARP scan focused on active devices"""
    print(f"\n[1/3] OT ARP Discovery - {network_range}")

    try:
        arp = ARP(pdst=network_range)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp

        result = srp(packet, timeout=timeout, verbose=False)[0]

        devices = []
        for sent, received in result:
            devices.append({
                'ip': received.psrc,
                'mac': received.hwsrc,
                'status': 'active',
                'method': 'ARP'
            })

        print(f"    ├─ Found {len(devices)} active devices via ARP")
        return devices

    except Exception as e:
        print(f"    └─ ARP scan failed: {e}")
        return []


def ot_protocol_scan(ip, timeout=1.0):
    """Scan for OT/ICS protocols on a specific IP"""
    detected_protocols = []

    # Scan critical OT ports first (highest priority)
    for port in CRITICAL_OT_PORTS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()

            if result == 0:
                protocol_name = OT_PROTOCOLS.get(port, f"Port {port}")
                detected_protocols.append({
                    'port': port,
                    'protocol': protocol_name,
                    'priority': 'critical'
                })
        except:
            pass

    # Scan common OT management ports
    for port in COMMON_OT_PORTS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()

            if result == 0:
                protocol_name = OT_PROTOCOLS.get(port, f"Port {port}")
                detected_protocols.append({
                    'port': port,
                    'protocol': protocol_name,
                    'priority': 'common'
                })
        except:
            pass

    # Extended scan only if device shows OT activity
    if detected_protocols:
        for port in EXTENDED_OT_PORTS:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout * 0.5)  # Faster for extended scan
                result = sock.connect_ex((ip, port))
                sock.close()

                if result == 0:
                    protocol_name = OT_PROTOCOLS.get(port, f"Port {port}")
                    detected_protocols.append({
                        'port': port,
                        'protocol': protocol_name,
                        'priority': 'extended'
                    })
            except:
                pass

    return detected_protocols


def ot_targeted_discovery(network_range, known_devices, max_workers=30):
    """Targeted scan for OT devices not found by ARP"""
    print(f"\n[2/3] OT Protocol Discovery - Scanning for industrial devices")

    try:
        network = ipaddress.IPv4Network(network_range)
        known_ips = set(device['ip'] for device in known_devices)

        # Focus on common OT IP ranges (often .100-200 range in industrial networks)
        target_ips = []
        for ip in network.hosts():
            ip_str = str(ip)
            last_octet = int(ip_str.split('.')[-1])

            # Prioritize common OT device IP ranges
            if ip_str not in known_ips:
                if 10 <= last_octet <= 50 or 100 <= last_octet <= 200:  # Common OT ranges
                    target_ips.insert(0, ip_str)  # High priority
                else:
                    target_ips.append(ip_str)  # Lower priority

        print(f"    ├─ Scanning {len(target_ips)} potential OT device IPs")

        ot_devices = []
        discovery_lock = threading.Lock()

        def ot_discovery_worker(ip):
            # Quick ping first
            try:
                if platform.system().lower() == "windows":
                    cmd = ["ping", "-n", "1", "-w", "1000", ip]
                else:
                    cmd = ["ping", "-c", "1", "-W", "1", ip]

                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
                if result.returncode != 0:
                    return  # Device not responding to ping, skip
            except:
                return

            # Scan for OT protocols
            protocols = ot_protocol_scan(ip, timeout=0.8)

            if protocols:  # Only add devices with detected OT protocols
                with discovery_lock:
                    ot_devices.append({
                        'ip': ip,
                        'mac': None,
                        'status': 'active',
                        'method': 'OT-Protocol',
                        'protocols': protocols
                    })

        # Concurrent scanning
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(ot_discovery_worker, ip) for ip in target_ips]

            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 25 == 0:
                    print(f"    ├─ Scanned: {completed}/{len(target_ips)} IPs")

        print(f"    └─ Found {len(ot_devices)} additional OT devices")
        return ot_devices

    except Exception as e:
        print(f"    └─ OT discovery failed: {e}")
        return []


def enrich_ot_device(device):
    """Enrich device with OT-specific information"""
    ip = device['ip']

    # Get hostname
    try:
        original_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(2.0)
        hostname = socket.gethostbyaddr(ip)[0]
        socket.setdefaulttimeout(original_timeout)
    except:
        hostname = ip
        if 'original_timeout' in locals():
            socket.setdefaulttimeout(original_timeout)

    # Scan for OT protocols if not already done
    if 'protocols' not in device:
        protocols = ot_protocol_scan(ip, timeout=1.5)
        device['protocols'] = protocols

    # Determine device type based on protocols
    device_type = classify_ot_device(device.get('protocols', []))

    device.update({
        'hostname': hostname,
        'device_type': device_type
    })

    return device


def classify_ot_device(protocols):
    """Classify OT device based on detected protocols"""
    if not protocols:
        return "Unknown"

    protocol_names = [p['protocol'].lower() for p in protocols]
    ports = [p['port'] for p in protocols]

    # PLC/Controller Detection
    if 502 in ports or any('modbus' in p for p in protocol_names):
        return "PLC/Controller (Modbus)"
    elif 44818 in ports or any('ethernet/ip' in p for p in protocol_names):
        return "PLC/Controller (EtherNet/IP)"
    elif 102 in ports and any('s7' in p for p in protocol_names):
        return "PLC/Controller (Siemens S7)"
    elif 4840 in ports:
        return "OPC-UA Server/Client"
    elif 20000 in ports:
        return "RTU/Gateway (DNP3)"
    elif 47808 in ports:
        return "Building Controller (BACnet)"

    # HMI/SCADA Detection
    elif any(p in ports for p in [80, 443, 8080, 8443]) and len(protocols) > 1:
        return "HMI/SCADA Station"

    # Network Infrastructure
    elif 161 in ports and any(p in ports for p in [22, 23]):
        return "Network Switch/Router"

    # Engineering Station
    elif any(p in ports for p in [22, 3389, 5900]) and any(p in ports for p in [135, 445]):
        return "Engineering Station"

    # Historian/Database
    elif any(p in ports for p in [1433, 1521, 3306, 5432]):
        return "Historian/Database"

    else:
        return f"Industrial Device ({len(protocols)} protocols)"


# Main OT-focused scan
print("[*] Initializing OT/ICS Asset Discovery...")

try:
    network_range, interface = get_local_network()
    print(f"[*] Target network: {network_range}")
    print(f"[*] Interface: {interface}")
except Exception as e:
    network_range = "192.168.12.0/24"
    print(f"[*] Using fallback network: {network_range}")

print(f"[*] Scanning for industrial protocols: {len(ALL_OT_PORTS)} ports")
print(f"[*] Critical OT protocols: {', '.join(OT_PROTOCOLS[p] for p in CRITICAL_OT_PORTS if p in OT_PROTOCOLS)}")

# Step 1: ARP Discovery
devices = ot_arp_scan(network_range)
found_ips = set(device['ip'] for device in devices)

# Step 2: OT Protocol Discovery
ot_devices = ot_targeted_discovery(network_range, devices)
devices.extend(ot_devices)

# Step 3: Protocol Analysis & Enrichment
print(f"\n[3/3] OT Asset Analysis - Enriching {len(devices)} devices")

enriched_devices = []
for i, device in enumerate(devices):
    if (i + 1) % 3 == 0:
        print(f"    ├─ Analyzing device {i + 1}/{len(devices)}")

    try:
        enriched_device = enrich_ot_device(device)

        # Only include devices with OT relevance
        protocols = enriched_device.get('protocols', [])
        if protocols:  # Has industrial protocols
            enriched_devices.append(enriched_device)
        elif device.get('method') == 'ARP':  # Or discovered via ARP (potentially OT device)
            enriched_devices.append(enriched_device)

    except Exception as e:
        print(f"    ├─ Failed to analyze {device['ip']}: {e}")

print(f"    └─ Analysis complete: {len(enriched_devices)} OT-relevant devices")

# Display Results
print(f"\n" + "=" * 85)
print(f"[+] OT/ICS ASSET DISCOVERY RESULTS")
print("=" * 85)
print(f"{'IP':<16} {'Device Type':<25} {'Hostname':<20} {'Key Protocols'}")
print("=" * 85)

# Sort by IP and display
for device in sorted(enriched_devices, key=lambda x: ipaddress.IPv4Address(x['ip'])):
    ip = device['ip']
    device_type = device.get('device_type', 'Unknown')[:24]
    hostname = str(device.get('hostname', ip))[:19]

    # Show key protocols
    protocols = device.get('protocols', [])
    if protocols:
        # Show critical protocols first
        critical_protocols = [p for p in protocols if p.get('priority') == 'critical']
        if critical_protocols:
            key_protocols = ', '.join([f"{p['protocol']}" for p in critical_protocols[:3]])
        else:
            key_protocols = ', '.join([f"{p['protocol']}" for p in protocols[:3]])

        if len(protocols) > 3:
            key_protocols += f" (+{len(protocols) - 3})"
    else:
        key_protocols = "Network Device"

    print(f"{ip:<16} {device_type:<25} {hostname:<20} {key_protocols}")

print("=" * 85)

# OT-Specific Statistics
print(f"\n[+] OT/ICS ASSET SUMMARY:")
print(f"    Active OT devices found: {len(enriched_devices)}")

# Device type breakdown
device_types = {}
for d in enriched_devices:
    device_type = d.get('device_type', 'Unknown')
    device_types[device_type] = device_types.get(device_type, 0) + 1

print(f"\n[+] Device type breakdown:")
for device_type, count in sorted(device_types.items(), key=lambda x: x[1], reverse=True):
    print(f"    {device_type}: {count}")

# Protocol statistics
protocol_usage = {}
for d in enriched_devices:
    protocols = d.get('protocols', [])
    for protocol in protocols:
        protocol_name = protocol['protocol']
        protocol_usage[protocol_name] = protocol_usage.get(protocol_name, 0) + 1

if protocol_usage:
    print(f"\n[+] Most common OT protocols:")
    for protocol, count in sorted(protocol_usage.items(), key=lambda x: x[1], reverse=True)[:8]:
        print(f"    {protocol}: {count} device(s)")

# Security recommendations
critical_protocols_found = []
for d in enriched_devices:
    protocols = d.get('protocols', [])
    for protocol in protocols:
        if protocol.get('priority') == 'critical':
            critical_protocols_found.append(protocol['protocol'])

if critical_protocols_found:
    print(f"\n[!] SECURITY NOTICE:")
    print(f"    Found {len(set(critical_protocols_found))} different critical OT protocols")
    print(f"    Ensure proper network segmentation and monitoring")

print(f"\n[*] OT/ICS Asset Discovery Complete!")
print(f"[*] Ready for OT Asset Management integration")

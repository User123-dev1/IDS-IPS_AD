import sys
from pathlib import Path
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import platform
import argparse

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

print("="*70)
print("  COMPREHENSIVE NETWORK DISCOVERY")
print("  (Multi-Method: ICMP Ping + TCP Connect + ARP Cache)")
print("="*70)

# Parse arguments
parser = argparse.ArgumentParser(description='Network Discovery Scanner')
parser.add_argument('--range', default='192.168.12.1-254', help='IP range (e.g., 192.168.12.1-254)')
parser.add_argument('--threads', type=int, default=100, help='Number of threads')
args = parser.parse_args()

# Parse IP range
def parse_ip_range(ip_range):
    """Parse IP range like 192.168.12.1-254"""
    if '-' in ip_range:
        base, end = ip_range.rsplit('.', 1)
        if '-' in end:
            start_host, end_host = end.split('-')
            return base, int(start_host), int(end_host)
    return None, None, None

base_ip, start, end = parse_ip_range(args.range)
if not base_ip:
    print(f"[!] Invalid range format. Using default: 192.168.12.1-254")
    base_ip, start, end = "192.168.12", 1, 254

print(f"[*] Scanning range: {base_ip}.{start}-{end}")
print(f"[*] Threads: {args.threads}")

def ping_host(ip):
    """ICMP ping check"""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-w', '500', ip]
    
    try:
        output = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
        if output.returncode == 0:
            return ip, 'ping'
    except:
        pass
    return None, None

def tcp_connect_check(ip, ports=[80, 443, 22, 23, 502, 44818, 102, 445, 135, 139]):
    """TCP connection check (works even if ping is blocked)"""
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                return ip, 'tcp'
        except:
            pass
    return None, None

def scan_host(ip):
    """Try both ping and TCP to discover host"""
    # Try ping first
    result_ip, method = ping_host(ip)
    if result_ip:
        return result_ip, method
    
    # If ping fails, try TCP
    result_ip, method = tcp_connect_check(ip)
    if result_ip:
        return result_ip, method
    
    return None, None

def get_mac_from_arp_table(ip):
    """Get MAC from Windows ARP table"""
    try:
        output = subprocess.check_output(['arp', '-a', ip], universal_newlines=True)
        for line in output.split('\n'):
            if ip in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if ip in part and i + 1 < len(parts):
                        mac = parts[i + 1]
                        if '-' in mac or ':' in mac:
                            return mac.replace('-', ':')
        return None
    except:
        return None

def resolve_hostname(ip):
    """Get hostname"""
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return ip

def quick_port_check(ip, ports=[80, 443, 22, 23, 502, 44818, 102, 20000, 135, 139, 445, 631]):
    """Check common ports"""
    open_ports = []
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                open_ports.append(port)
        except:
            pass
    return open_ports

# Perform host discovery
print(f"\n[*] Discovering hosts...")
alive_hosts = []
discovery_methods = {}

with ThreadPoolExecutor(max_workers=args.threads) as executor:
    futures = {executor.submit(scan_host, f"{base_ip}.{i}"): i for i in range(start, end + 1)}
    
    completed = 0
    total = len(futures)
    
    for future in as_completed(futures):
        completed += 1
        if completed % 50 == 0 or completed == total:
            print(f"  Progress: {completed}/{total} ({100*completed//total}%)")
        
        result_ip, method = future.result()
        if result_ip:
            alive_hosts.append(result_ip)
            discovery_methods[result_ip] = method
            print(f"  [+] Found: {result_ip} (via {method})")

print(f"\n[+] Found {len(alive_hosts)} alive hosts")
print("="*70)

# Enrich with details
from scanner.network_scanner import EnterpriseNetworkScanner
scanner = EnterpriseNetworkScanner()

devices = []
print(f"\n{'IP':<18} {'MAC':<20} {'Vendor':<25} {'Hostname':<20}")
print("="*70)

for ip in sorted(alive_hosts, key=lambda x: [int(p) for p in x.split('.')]):
    mac = get_mac_from_arp_table(ip)
    
    if mac:
        vendor = scanner._get_vendor_from_mac(mac)
    else:
        mac = "Unknown"
        vendor = "Unknown"
    
    hostname = resolve_hostname(ip)
    ports = quick_port_check(ip)
    
    method = discovery_methods.get(ip, 'unknown')
    print(f"{ip:<18} {mac:<20} {vendor:<25} {hostname:<20}")
    
    if ports:
        print(f"    -> Open ports: {', '.join(map(str, ports))}")
    
    devices.append({
        'ip': ip,
        'mac': mac,
        'vendor': vendor,
        'hostname': hostname,
        'open_ports': ports,
        'status': 'online',
        'discovery_method': method
    })

print("="*70)
print(f"\n[OK] Discovery complete: {len(devices)} devices found")

# Breakdown by vendor
print("\n" + "="*70)
print("  DEVICE BREAKDOWN")
print("="*70)

vendors = {}
ot_devices = []

for d in devices:
    v = d.get('vendor', 'Unknown')
    vendors[v] = vendors.get(v, 0) + 1
    
    # Identify OT/ICS devices
    ot_vendors = ['Rockwell', 'Siemens', 'Schneider', 'ABB', 'Honeywell', 'Emerson', 'GE']
    if any(ot in v for ot in ot_vendors) or any(p in d['open_ports'] for p in [502, 44818, 102, 20000]):
        ot_devices.append(d)

print("\nBy Vendor:")
for vendor, count in sorted(vendors.items(), key=lambda x: x[1], reverse=True):
    print(f"  {vendor:<30} {count:>3} device(s)")

print("\nBy Discovery Method:")
methods = {}
for d in devices:
    m = d.get('discovery_method', 'unknown')
    methods[m] = methods.get(m, 0) + 1
for method, count in methods.items():
    print(f"  {method:<30} {count:>3} device(s)")

if ot_devices:
    print("\n" + "="*70)
    print(f"  [OT/ICS] FOUND {len(ot_devices)} INDUSTRIAL DEVICES - PRIORITY TARGETS!")
    print("="*70)
    for d in ot_devices:
        ports_str = ', '.join(map(str, d['open_ports'])) if d['open_ports'] else 'None'
        print(f"  * {d['ip']:<18} {d['vendor']:<25} Ports: {ports_str}")

print("\n[*] Next: python full_network_scan.py --targets <IP1> <IP2> ...")


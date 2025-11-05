import sys
from pathlib import Path
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import platform

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

print("="*70)
print("  NETWORK DISCOVERY - SIMPLE & FAST")
print("="*70)
print("\n[*] Starting scan of 192.168.12.1-254...")
print("[*] This will take about 30-60 seconds...\n")

def scan_host(ip):
    """Quick check if host is alive"""
    # Method 1: Try TCP connection on common ports
    common_ports = [80, 443, 22, 445, 502, 44818]
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                return ip, 'tcp', port
        except:
            pass
    
    # Method 2: Try ping
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-w', '300', ip]
    
    try:
        output = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.5)
        if output.returncode == 0:
            return ip, 'ping', None
    except:
        pass
    
    return None, None, None

def get_mac_from_arp(ip):
    """Get MAC from ARP table"""
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
    except:
        pass
    return "Unknown"

def get_hostname(ip):
    """Get hostname"""
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return ip

# Scan network
alive_hosts = []
base = "192.168.12"

print("[*] Scanning... (dots = progress)\n")

with ThreadPoolExecutor(max_workers=100) as executor:
    futures = {executor.submit(scan_host, f"{base}.{i}"): i for i in range(1, 255)}
    
    completed = 0
    for future in as_completed(futures):
        completed += 1
        
        # Show progress dots
        if completed % 25 == 0:
            print(f"  [{completed}/254]", flush=True)
        
        result_ip, method, port = future.result()
        if result_ip:
            alive_hosts.append((result_ip, method, port))
            print(f"  [+] FOUND: {result_ip} (via {method})", flush=True)

print(f"\n{'='*70}")
print(f"[+] Discovery complete: Found {len(alive_hosts)} devices\n")

# Show details
from scanner.network_scanner import EnterpriseNetworkScanner
scanner = EnterpriseNetworkScanner()

print(f"{'IP':<18} {'MAC':<20} {'Vendor':<25} {'Hostname'}")
print("="*70)

for ip, method, port in sorted(alive_hosts, key=lambda x: [int(p) for p in x[0].split('.')]):
    mac = get_mac_from_arp(ip)
    vendor = scanner._get_vendor_from_mac(mac) if mac != "Unknown" else "Unknown"
    hostname = get_hostname(ip)
    
    print(f"{ip:<18} {mac:<20} {vendor:<25} {hostname}")

print("="*70)
print(f"\n[OK] Found {len(alive_hosts)} devices on network")


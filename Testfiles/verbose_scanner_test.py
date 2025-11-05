"""
Verbose Network Scanner Diagnostic
This will show EXACTLY what happens during each scan step
"""

import socket
import subprocess
import platform
import sys
import time

def test_single_ip(ip):
    """Test a single IP with all methods and show results"""
    print(f"\n{'='*60}")
    print(f"  TESTING IP: {ip}")
    print(f"{'='*60}")
    
    # Test 1: Can we reach it at all?
    print(f"\n[1] Basic Connectivity Test")
    print(f"    Testing socket connection to {ip}...")
    
    # Test 2: Ping test
    print(f"\n[2] ICMP Ping Test")
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'
        
        command = ['ping', param, '1', timeout_param, '1000' if platform.system().lower() == 'windows' else '1', ip]
        
        print(f"    Command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=3
        )
        
        if result.returncode == 0:
            print(f"    ✅ PING SUCCESS - Host is alive!")
        else:
            print(f"    ❌ PING FAILED - No ICMP response")
            print(f"    (This is OK - many devices block ping)")
    except Exception as e:
        print(f"    ❌ PING ERROR: {e}")
    
    # Test 3: TCP Port Scan
    print(f"\n[3] TCP Port Scan Test")
    common_ports = [80, 443, 445, 22, 3389, 139, 135, 21, 23, 25, 502, 8080]
    found_ports = []
    
    print(f"    Scanning {len(common_ports)} common ports...")
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((ip, port))
            
            if result == 0:
                print(f"    ✅ Port {port} OPEN")
                found_ports.append(port)
            else:
                print(f"    ⚫ Port {port} closed", end='\r')
            
            sock.close()
        except Exception as e:
            print(f"    ❌ Port {port} error: {e}")
    
    if found_ports:
        print(f"\n    ✅ FOUND {len(found_ports)} OPEN PORTS: {found_ports}")
    else:
        print(f"\n    ❌ NO OPEN PORTS FOUND")
    
    # Test 4: Hostname resolution
    print(f"\n[4] Hostname Resolution Test")
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        print(f"    ✅ Hostname: {hostname}")
    except:
        print(f"    ⚫ No hostname (this is normal)")
    
    # Test 5: ARP (MAC address)
    print(f"\n[5] ARP/MAC Address Test")
    try:
        if platform.system().lower() == 'windows':
            result = subprocess.check_output(f'arp -a {ip}', shell=True, timeout=2).decode('utf-8', errors='ignore')
            if 'No ARP' not in result and ip in result:
                print(f"    ✅ ARP entry found")
                print(f"    {result.strip()}")
            else:
                print(f"    ⚫ No ARP entry")
    except Exception as e:
        print(f"    ⚫ Could not get ARP: {e}")
    
    # Final verdict
    print(f"\n{'='*60}")
    print(f"  VERDICT FOR {ip}:")
    print(f"{'='*60}")
    
    if found_ports:
        print(f"  ✅ HOST IS ALIVE - Has {len(found_ports)} open port(s)")
        print(f"  🔹 Scanner SHOULD detect this device")
        return True
    else:
        print(f"  ❌ HOST APPEARS OFFLINE")
        print(f"  🔹 No open ports, no ping response")
        print(f"  🔹 Scanner will skip this device")
        return False

def test_network_range(subnet):
    """Test a few IPs in the subnet"""
    print(f"\n{'#'*60}")
    print(f"  NETWORK RANGE TEST: {subnet}")
    print(f"{'#'*60}")
    
    import ipaddress
    network = ipaddress.ip_network(subnet, strict=False)
    
    # Test first 5 IPs
    test_ips = list(network.hosts())[:5]
    
    print(f"\nTesting first 5 IPs in range...")
    alive_count = 0
    
    for ip in test_ips:
        if test_single_ip(str(ip)):
            alive_count += 1
        time.sleep(0.5)
    
    print(f"\n{'='*60}")
    print(f"  SUMMARY: Found {alive_count} alive host(s) out of {len(test_ips)} tested")
    print(f"{'='*60}\n")
    
    return alive_count

def test_known_host():
    """Test against known hosts that should exist"""
    print(f"\n{'#'*60}")
    print(f"  TESTING KNOWN HOSTS")
    print(f"{'#'*60}")
    
    # Test localhost
    print(f"\n🔹 Testing localhost (127.0.0.1)...")
    test_single_ip("127.0.0.1")
    
    # Test default gateway
    print(f"\n🔹 Testing default gateway...")
    try:
        if platform.system().lower() == 'windows':
            result = subprocess.check_output('ipconfig', shell=True).decode('utf-8', errors='ignore')
            import re
            gateways = re.findall(r'Default Gateway.*?:\s+(\d+\.\d+\.\d+\.\d+)', result)
            if gateways:
                gateway = gateways[0]
                print(f"   Found gateway: {gateway}")
                test_single_ip(gateway)
            else:
                print("   ⚫ No gateway found")
    except Exception as e:
        print(f"   ❌ Error finding gateway: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  VERBOSE NETWORK SCANNER DIAGNOSTIC")
    print("="*60)
    
    # Test 1: Known hosts
    test_known_host()
    
    # Test 2: Your subnet
    print(f"\n{'#'*60}")
    subnet = input("\nEnter subnet to test (e.g., 192.168.12.0/24): ").strip()
    if subnet:
        test_network_range(subnet)
    
    print("\n" + "="*60)
    print("  DIAGNOSTIC COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("  1. If NO ports were found on ANY device → Check firewall")
    print("  2. If gateway/localhost work → Network scanning is functional")
    print("  3. If your subnet IPs don't respond → They might be offline")
    print("  4. If some ports found → Scanner code needs debugging")
    print("="*60 + "\n")

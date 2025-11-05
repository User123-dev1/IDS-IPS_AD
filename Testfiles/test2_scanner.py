import sys
import os
import socket

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*60)
print("  IP SCAN TEST")
print("="*60)

ip = input("\nEnter IP to test: ").strip()

# Manual port scan
print("\nScanning", ip, "manually...")
ports = [80, 443, 445, 22, 3389, 139, 135, 502, 8080]
found = []

for port in ports:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        if sock.connect_ex((ip, port)) == 0:
            found.append(port)
            print("  Port", port, "OPEN")
        sock.close()
    except:
        pass

if found:
    print("\n[MANUAL] Found", len(found), "open ports:", found)
else:
    print("\n[MANUAL] No open ports found")

# Test with actual scanner
print("\n" + "="*60)
print("Testing with scanner...")
print("="*60)

try:
    from core.network_scanner import EnterpriseNetworkScanner
    scanner = EnterpriseNetworkScanner()
    result = scanner._scan_host(ip)
    
    if result:
        print("\n[SCANNER] SUCCESS - Found device!")
        print("  Device Type:", result['device_type'])
        print("  Open Ports:", result['open_ports'])
    else:
        print("\n[SCANNER] FAILED - No device found")
        if found:
            print("\nPROBLEM: Manual scan found", len(found), "ports")
            print("         But scanner found nothing!")
            print("         Scanner code is broken.")
        
except Exception as e:
    print("\n[ERROR]", e)

print("\n" + "="*60)

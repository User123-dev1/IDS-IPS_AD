import sys
import os
sys.path.insert(0, '../src')

print("="*60)
print("  DIRECT SCANNER TEST")
print("="*60)

try:
    from core.network_scanner import EnterpriseNetworkScanner
    print("\n[OK] Scanner module imported")
    
    scanner = EnterpriseNetworkScanner(max_workers=10)
    print("[OK] Scanner created")
    
    subnet = input("\nEnter subnet (e.g. 192.168.12.0/28): ").strip()
    
    print("\nScanning", subnet, "...")
    print("This will take a moment...\n")
    
    devices = scanner.scan_multiple_subnets([subnet])
    
    print("\n" + "="*60)
    print("  RESULTS")
    print("="*60)
    print("Found", len(devices), "device(s)")
    
    if devices:
        for d in devices:
            print("\n  IP:", d['ip_address'])
            print("  Hostname:", d['hostname'])
            print("  Type:", d['device_type'])
            print("  Ports:", d['open_ports'])
    else:
        print("\nNO DEVICES FOUND")
        print("\nThis could mean:")
        print("  1. Subnet is empty")
        print("  2. Scanner code is broken")
        print("  3. Firewall blocking scans")
        
except Exception as e:
    print("\n[ERROR]", e)
    import traceback
    traceback.print_exc()

print("\n" + "="*60)

import sys
sys.path.insert(0, '../src')

from core.network_scanner import EnterpriseNetworkScanner

print("\n" + "="*60)
print("  TESTING FIXED NETWORK SCANNER")
print("="*60 + "\n")

# Test on a small range
scanner = EnterpriseNetworkScanner(max_workers=10)

print("Testing on 192.168.12.0/28 (16 hosts)...")
print("This should find devices even if they block ping!\n")

devices = scanner.scan_multiple_subnets(["192.168.12.0/28"])

print(f"\n✅ RESULT: Found {len(devices)} device(s)")

if devices:
    print("\nDevices discovered:")
    for device in devices:
        print(f"  • {device['ip_address']:15} - {device['hostname']:25} ({device['device_type']})")
        if device['open_ports']:
            print(f"    Ports: {', '.join(map(str, device['open_ports'][:5]))}")
else:
    print("\n⚠ No devices found. This could mean:")
    print("  1. Network is truly empty")
    print("  2. Firewall blocking outbound scans")
    print("  3. Need administrator rights")
    print("  4. Try a different subnet (your actual network)")

print("\n" + "="*60 + "\n")

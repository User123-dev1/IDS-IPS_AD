import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scanner.network_scanner import EnterpriseNetworkScanner

print("="*70)
print("  TESTING SCANNER DIRECTLY (NOT GUI)")
print("="*70)

scanner = EnterpriseNetworkScanner()

# Test the known working IPs from your report
test_ips = [
    "192.168.12.228",  # Rockwell PLC
    "192.168.12.162",  # Siemens
    "192.168.12.174",  # Cisco
    "192.168.12.190",  # Windows Server
]

print("\n[*] Testing scanner on known devices...")
for ip in test_ips:
    print(f"\n[*] Scanning {ip}...")
    try:
        result = scanner.scan_target(ip)
        print(f"    Status: {result['status']}")
        print(f"    Vendor: {result['vendor']}")
        print(f"    Hostname: {result['hostname']}")
    except Exception as e:
        print(f"    ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n[OK] Direct scanner test complete!")


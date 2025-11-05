import sys
from pathlib import Path

print("="*60)
print("  PLC DETAILED SCANNER")
print("="*60)

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from scanner.network_scanner import EnterpriseNetworkScanner

scanner = EnterpriseNetworkScanner()

print("\nScanning PLC at 192.168.12.228...")
print("Looking for industrial protocols...\n")

# Deep scan the PLC
result = scanner._scan_host("192.168.12.228")

print("="*60)
print("  PLC DETAILS")
print("="*60)
if result:
    for key, value in result.items():
        print(f"  {key}: {value}")
else:
    print("  [ERROR] No result returned")

print("\n" + "="*60)

# Also try a broader scan to find more PLCs
print("\nScanning entire subnet for industrial devices...")
devices = scanner.scan_multiple_subnets(["192.168.12.0/24"])

plcs = [d for d in devices if d.get('device_type') in ['PLC', 'Industrial Controller', 'HMI']]
print(f"\nFound {len(plcs)} industrial devices:")
for plc in plcs:
    print(f"\n  IP: {plc['ip_address']}")
    print(f"  Type: {plc['device_type']}")
    print(f"  Ports: {plc['open_ports']}")

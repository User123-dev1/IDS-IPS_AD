import sys
from pathlib import Path

print("="*60)
print("  SUBNET SCANNER - Finding all devices")
print("="*60)

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from scanner.network_scanner import EnterpriseNetworkScanner

# Scan your subnet
print("\nScanning subnet: 192.168.12.0/24")
print("This will scan IPs: 192.168.12.1 - 192.168.12.14")
print("Please wait...\n")

scanner = EnterpriseNetworkScanner()
devices = scanner.scan_multiple_subnets(["192.168.12.0/24"])

print("="*60)
print(f"  FOUND {len(devices)} DEVICES")
print("="*60)

if devices:
    for i, device in enumerate(devices, 1):
        print(f"\n[Device {i}]")
        print(f"  IP: {device.get('ip_address')}")
        print(f"  Hostname: {device.get('hostname')}")
        print(f"  Type: {device.get('device_type')}")
        print(f"  Ports: {device.get('open_ports')}")
        print(f"  MAC: {device.get('mac_address', 'Unknown')}")
else:
    print("\n[WARNING] No devices found!")
    print("This might mean:")
    print("  - Firewall is blocking scans")
    print("  - No other devices are online")
    print("  - Scanner timeout too short")

print("\n" + "="*60)

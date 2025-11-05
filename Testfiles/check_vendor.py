import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

print("Checking vendor detection system...")
print("="*60)

# Check if mac_vendor_lookup exists
try:
    from scanner.network_scanner import EnterpriseNetworkScanner
    scanner = EnterpriseNetworkScanner()
    
    # Look for MAC vendor lookup method
    print("\nMethods for MAC lookup:")
    for attr in dir(scanner):
        if 'mac' in attr.lower() or 'vendor' in attr.lower():
            print(f"  - {attr}")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60)

# Check if there's a vendor database file
print("\nLooking for vendor database files...")
import os
for root, dirs, files in os.walk(project_root / "src"):
    for file in files:
        if 'vendor' in file.lower() or 'oui' in file.lower() or 'mac' in file.lower():
            print(f"  Found: {os.path.join(root, file)}")

print("\n" + "="*60)

# Test MAC lookup manually
mac = "00:1D:9C:A6:67:52"
oui = mac[:8]  # First 3 octets
print(f"\nMAC: {mac}")
print(f"OUI: {oui}")
print(f"Should be: Rockwell Automation / Allen Bradley")

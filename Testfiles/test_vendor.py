import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

print("="*60)
print("  VENDOR LOOKUP TEST")
print("="*60)

from mac_vendor_lookup import MacLookup

mac_lookup = MacLookup()
mac = "00:1D:9C:A6:67:52"

try:
    vendor = mac_lookup.lookup(mac)
    print(f"\nMAC: {mac}")
    print(f"Vendor: {vendor}")
    print("\nSUCCESS! Vendor detection working!")
except Exception as e:
    print(f"Error: {e}")
    print("Updating vendor database...")
    mac_lookup.update_vendors()
    vendor = mac_lookup.lookup(mac)
    print(f"\nMAC: {mac}")
    print(f"Vendor: {vendor}")

print("\n" + "="*60)

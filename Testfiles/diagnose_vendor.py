import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

print("="*60)
print("  VENDOR LOOKUP DIAGNOSTICS")
print("="*60)

from scanner.network_scanner import EnterpriseNetworkScanner
import inspect

scanner = EnterpriseNetworkScanner()

# Show the current implementation
print("\nCurrent _get_vendor_from_mac implementation:")
print("-"*60)
source = inspect.getsource(scanner._get_vendor_from_mac)
print(source)

# Test it
print("="*60)
print("\nTesting vendor lookup:")
mac = "00:1D:9C:A6:67:52"
vendor = scanner._get_vendor_from_mac(mac)
print(f"  MAC: {mac}")
print(f"  Result: {vendor}")
print(f"  Expected: Rockwell Automation")

# Check if mac-vendor-lookup is installed
print("\n" + "="*60)
print("Checking installed libraries:")
try:
    import mac_vendor_lookup
    print("  ✓ mac-vendor-lookup is installed")
    
    # Test it directly
    mac_lookup = mac_vendor_lookup.MacLookup()
    try:
        vendor = mac_lookup.lookup(mac)
        print(f"  Direct lookup result: {vendor}")
    except Exception as e:
        print(f"  Direct lookup error: {e}")
        print("  Trying to update database...")
        mac_lookup.update_vendors()
        vendor = mac_lookup.lookup(mac)
        print(f"  After update: {vendor}")
        
except ImportError:
    print("  ✗ mac-vendor-lookup NOT installed")
    print("\n  Install it with: pip install mac-vendor-lookup")

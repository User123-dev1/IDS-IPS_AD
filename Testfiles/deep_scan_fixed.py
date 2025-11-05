import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scanner.network_scanner import EnterpriseNetworkScanner

print("="*70)
print("  DEEP OT/ICS SECURITY SCAN")
print("="*70)

# Priority targets
targets = [
    "192.168.12.228",  # PLC
    "192.168.12.161",  # VPN device
    "192.168.12.162",  # Network device
    "192.168.12.174",  # Cisco router
    "192.168.12.190",  # Research server
]

scanner = EnterpriseNetworkScanner()

print(f"\n[*] Available scanner methods:")
methods = [m for m in dir(scanner) if not m.startswith('_') and callable(getattr(scanner, m))]
for m in methods:
    print(f"  - {m}")

print(f"\n[*] Scanning {len(targets)} priority devices...\n")

for ip in targets:
    print(f"\n{'='*70}")
    print(f"  Scanning: {ip}")
    print(f"{'='*70}")
    
    try:
        # Try different method names
        if hasattr(scanner, 'scan_target'):
            result = scanner.scan_target(ip)
        elif hasattr(scanner, 'scan'):
            result = scanner.scan(ip)
        elif hasattr(scanner, 'scan_host'):
            result = scanner.scan_host(ip)
        elif hasattr(scanner, 'scan_device'):
            result = scanner.scan_device(ip)
        else:
            print(f"[ERROR] No scan method found! Available: {methods}")
            break
        
        print(f"\nResult: {result}")
        
    except Exception as e:
        print(f"[ERROR] Failed to scan {ip}: {e}")
        import traceback
        traceback.print_exc()


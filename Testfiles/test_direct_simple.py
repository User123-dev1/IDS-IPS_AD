import socket
import sys
from pathlib import Path

print("="*60)
print("  DIRECT SCANNER TEST")
print("="*60)

# Find the scanner module
project_root = Path(__file__).parent
possible_paths = [
    project_root / "src",
    project_root / "core",
    project_root,
]

print("\nSearching for scanner module...")
for p in possible_paths:
    scanner_file = p / "network_scanner.py"
    if not scanner_file.exists():
        scanner_file = p / "core" / "network_scanner.py"
    
    if scanner_file.exists():
        print(f"  [FOUND] {scanner_file}")
        sys.path.insert(0, str(p))
        break
else:
    print("  [ERROR] Cannot find network_scanner.py")
    print("\nProject structure:")
    for item in project_root.rglob("*.py"):
        print(f"    {item.relative_to(project_root)}")
    sys.exit(1)

# Now try to import
try:
    from core.network_scanner import EnterpriseNetworkScanner
    print("[OK] Module imported!\n")
except ImportError as e:
    print(f"[ERROR] Cannot import: {e}")
    sys.exit(1)

# Test scanning
scanner = EnterpriseNetworkScanner()
print("Testing scan on 192.168.12.190 (your machine)...")
result = scanner._scan_host("192.168.12.190")

print("\n" + "="*60)
if result:
    print("  SUCCESS - Scanner found device!")
    print("  Type:", result.get("device_type"))
    print("  Ports:", result.get("open_ports"))
else:
    print("  FAILED - Scanner returned None")
    print("\n  Manual test:")
    found = []
    for port in [80, 443, 445, 135, 139]:
        sock = socket.socket()
        sock.settimeout(0.5)
        if sock.connect_ex(("192.168.12.190", port)) == 0:
            found.append(port)
        sock.close()
    print(f"  Manual scan found: {found}")
print("="*60)

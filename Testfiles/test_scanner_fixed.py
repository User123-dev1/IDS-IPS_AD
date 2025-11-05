import socket
import sys
from pathlib import Path

print("="*60)
print("  DIRECT SCANNER TEST")
print("="*60)

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Import with CORRECT path
try:
    from scanner.network_scanner import EnterpriseNetworkScanner
    print("[OK] Module imported successfully!\n")
except ImportError as e:
    print(f"[ERROR] Cannot import: {e}")
    sys.exit(1)

# Test scanning YOUR machine (we know it has open ports)
print("Testing scan on 192.168.12.190 (your machine)...")
print("We know these ports are open: [80, 445, 135]\n")

scanner = EnterpriseNetworkScanner()
result = scanner._scan_host("192.168.12.190")

print("="*60)
if result:
    print("  [SUCCESS] Scanner found device!")
    print(f"  Device Type: {result.get('device_type')}")
    print(f"  Open Ports: {result.get('open_ports')}")
    print(f"  IP Address: {result.get('ip_address')}")
    print(f"  Hostname: {result.get('hostname')}")
else:
    print("  [FAILED] Scanner returned None")
    print("\n  Doing manual verification:")
    found = []
    for port in [80, 443, 445, 135, 139, 22, 23, 502]:
        sock = socket.socket()
        sock.settimeout(1)
        if sock.connect_ex(("192.168.12.190", port)) == 0:
            found.append(port)
        sock.close()
    print(f"  Manual scan found these ports: {found}")
print("="*60)

import sys
sys.path.insert(0, '../src')
from core.network_scanner import EnterpriseNetworkScanner

scanner = EnterpriseNetworkScanner()
print(f"\nTesting {testIP}...\n")
result = scanner._scan_host('192.168.12.1')

if result:
    print(f"\n✅ FOUND DEVICE!")
    for key, value in result.items():
        print(f"  {key}: {value}")
else:
    print(f"\n❌ No response from 192.168.12.1")
    print(f"   Device is offline or blocking all scan attempts")

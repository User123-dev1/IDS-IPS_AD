import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from scanner.network_scanner import EnterpriseNetworkScanner

scanner = EnterpriseNetworkScanner()

print("Available methods in EnterpriseNetworkScanner:")
print("="*60)
for method in dir(scanner):
    if not method.startswith('_'):
        print(f"  - {method}")
print("="*60)

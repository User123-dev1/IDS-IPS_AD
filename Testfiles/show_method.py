import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

import inspect
from scanner.network_scanner import EnterpriseNetworkScanner

scanner = EnterpriseNetworkScanner()

print("Current _get_vendor_from_mac code:")
print("="*60)
print(inspect.getsource(scanner._get_vendor_from_mac))
print("="*60)

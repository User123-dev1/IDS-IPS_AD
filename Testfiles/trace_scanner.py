"""
Scanner Execution Tracer
This will trace exactly what the scanner is doing
"""

import sys
sys.path.insert(0, '../src')

from core.network_scanner import EnterpriseNetworkScanner
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Monkey-patch the scanner to add verbose output
original_scan_host = EnterpriseNetworkScanner._scan_host

def verbose_scan_host(self, ip):
    print(f"\n🔍 Scanning {ip}...")
    result = original_scan_host(ip)
    
    if result:
        print(f"   ✅ Found device: {result['ip_address']} ({result['device_type']})")
    else:
        print(f"   ⚫ No response from {ip}")
    
    return result

EnterpriseNetworkScanner._scan_host = verbose_scan_host

# Run scan
print("\n" + "="*60)
print("  TRACING SCANNER EXECUTION")
print("="*60 + "\n")

subnet = input("Enter subnet to scan (e.g., 192.168.12.0/28): ").strip()

if subnet:
    print(f"\nStarting scan of {subnet}...")
    print("This will show EXACTLY what the scanner does for each IP.\n")
    
    scanner = EnterpriseNetworkScanner(max_workers=5)
    devices = scanner.scan_multiple_subnets([subnet])
    
    print("\n" + "="*60)
    print(f"  RESULT: Found {len(devices)} device(s)")
    print("="*60)
    
    if devices:
        for device in devices:
            print(f"  • {device['ip_address']} - {device['hostname']} ({device['device_type']})")
    else:
        print("\n⚠ NO DEVICES FOUND")
        print("\nPossible reasons:")
        print("  1. Subnet is empty (no devices online)")
        print("  2. All devices block ping AND have no open ports")
        print("  3. Firewall blocking outbound connections")
        print("  4. Scanner logic issue")
        
    print("\n" + "="*60 + "\n")

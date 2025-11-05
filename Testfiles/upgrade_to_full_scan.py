import re

print("[*] Reading main_window.py...")
with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the start_enterprise_scan method and replace the scanning logic
pattern = r'(priority_devices = \[.*?\])'

replacement = '''# Scan full subnet to find ALL devices
            subnet_ranges = []
            for line in subnet_text.split('\\n'):
                line = line.strip()
                if line and '/' in line:
                    subnet_ranges.append(line)
            
            if not subnet_ranges:
                subnet_ranges = ["192.168.12.0/24"]
            
            # Generate list of IPs to scan from subnet
            import ipaddress
            priority_devices = []
            for subnet in subnet_ranges:
                try:
                    network = ipaddress.ip_network(subnet, strict=False)
                    # Scan all IPs in subnet (skip .0 and .255)
                    for ip in network.hosts():
                        priority_devices.append(str(ip))
                except Exception as e:
                    self.log(f"[ERROR] Invalid subnet {subnet}: {e}")
            
            self.log(f"[*] Scanning {len(priority_devices)} IPs in subnet {subnet_text}...")'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open("../src/gui/main_window.py", "w", encoding="utf-8") as f:
    f.write(content)

print("[OK] Scanner now scans FULL SUBNET!")
print("[*] Will find all 9-10 devices instead of just 5")


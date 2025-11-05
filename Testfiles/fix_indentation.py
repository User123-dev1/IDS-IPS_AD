import re

print("[*] Fixing indentation in main_window.py...")

with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find line 921 (the function definition)
for i, line in enumerate(lines):
    if i == 920:  # Line 921 (0-indexed)
        print(f"Line 921: {line.strip()}")
    if i == 921:  # Line 922
        print(f"Line 922: {line.strip()}")

# Find and fix the problematic function
fixed_lines = []
inside_enterprise_scan = False
for i, line in enumerate(lines):
    # Check if this is the start_enterprise_scan definition
    if 'def start_enterprise_scan(self):' in line:
        inside_enterprise_scan = True
        # Ensure it has correct indentation (should be 4 spaces as a class method)
        fixed_lines.append('    def start_enterprise_scan(self):\n')
        continue
    
    # If we're inside the method and this is the docstring
    if inside_enterprise_scan and '"""Start enterprise network scan' in line:
        fixed_lines.append('        """Start enterprise network scan - FIXED VERSION"""\n')
        continue
    
    # If we're inside the method and hit 'try:'
    if inside_enterprise_scan and line.strip() == 'try:':
        fixed_lines.append('        try:\n')
        inside_enterprise_scan = False  # Stop special handling
        continue
    
    fixed_lines.append(line)

# Save fixed version
with open("../src/gui/main_window.py", "w", encoding="utf-8") as f:
    f.writelines(fixed_lines)

print("[OK] Fixed indentation!")


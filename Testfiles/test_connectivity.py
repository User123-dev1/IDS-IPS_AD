"""
Basic Network Connectivity Test
"""

import socket
import subprocess
import platform

print("\n" + "="*60)
print("  BASIC CONNECTIVITY TEST")
print("="*60 + "\n")

# Test 1: Can we create sockets?
print("[1] Socket Creation Test...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.close()
    print("    ✅ Can create sockets")
except Exception as e:
    print(f"    ❌ Socket error: {e}")

# Test 2: Can we ping localhost?
print("\n[2] Localhost Test...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', 80))
    sock.close()
    
    if result == 0:
        print("    ✅ Localhost port 80 is open")
    else:
        print("    ⚫ Localhost port 80 closed (normal)")
except Exception as e:
    print(f"    ❌ Error: {e}")

# Test 3: Can we reach internet?
print("\n[3] Internet Connectivity Test...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('8.8.8.8', 53))
    sock.close()
    
    if result == 0:
        print("    ✅ Can reach internet (8.8.8.8:53)")
    else:
        print("    ⚫ No internet connection (normal for isolated networks)")
except Exception as e:
    print(f"    ⚫ Internet test: {e}")

# Test 4: Get local IP
print("\n[4] Local Network Info...")
try:
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"    ✅ Hostname: {hostname}")
    print(f"    ✅ Local IP: {local_ip}")
except Exception as e:
    print(f"    ❌ Error: {e}")

# Test 5: Check if running as admin
print("\n[5] Permission Check...")
try:
    import ctypes
    is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    if is_admin:
        print("    ✅ Running as Administrator")
    else:
        print("    ⚠ NOT running as Administrator")
        print("       (May limit network scanning capabilities)")
except:
    print("    ⚫ Cannot determine admin status")

print("\n" + "="*60)
print("\nBasic connectivity looks OK? [Y/N]: ", end='')
import sys
response = sys.stdin.readline().strip()

if response.lower() == 'y':
    print("\n✅ Good! Network basics are working.")
    print("   The issue is likely in the scanner logic or firewall.\n")
else:
    print("\n⚠ There may be fundamental network issues.")
    print("   Check firewall settings and network adapter.\n")

print("="*60 + "\n")

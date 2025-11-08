"""
Packet Capture Diagnostic Tool
Tests if packet capture is working on your system
Run as Administrator!
"""

import sys
import os

print("=" * 70)
print("PACKET CAPTURE DIAGNOSTIC TOOL")
print("=" * 70)
print()

# Check 1: Administrator privileges
print("[1] Checking Administrator privileges...")
try:
    import ctypes
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    if is_admin:
        print("    ✓ Running as Administrator")
    else:
        print("    ✗ NOT running as Administrator!")
        print("    → Right-click PowerShell → 'Run as Administrator'")
        print("    → Then run this script again")
        input("\nPress Enter to exit...")
        sys.exit(1)
except:
    print("    ? Could not check (not Windows?)")

# Check 2: Scapy installation
print("\n[2] Checking Scapy installation...")
try:
    import scapy
    from scapy.all import get_if_list, sniff, IP, TCP, UDP, ICMP
    print(f"    ✓ Scapy version: {scapy.__version__}")
except ImportError as e:
    print(f"    ✗ Scapy not installed: {e}")
    print("    → Install: pip install scapy")
    input("\nPress Enter to exit...")
    sys.exit(1)

# Check 3: Npcap service (Windows)
print("\n[3] Checking Npcap service...")
try:
    import subprocess
    result = subprocess.run(['sc', 'query', 'npcap'],
                          capture_output=True, text=True, timeout=5)
    if 'RUNNING' in result.stdout:
        print("    ✓ Npcap service is running")
    else:
        print("    ✗ Npcap service not running!")
        print("    → Install Npcap from: https://npcap.com/")
        input("\nPress Enter to exit...")
        sys.exit(1)
except Exception as e:
    print(f"    ? Could not check Npcap: {e}")

# Check 4: Network interfaces
print("\n[4] Checking network interfaces...")
try:
    interfaces = get_if_list()
    print(f"    Found {len(interfaces)} interface(s):")
    for i, iface in enumerate(interfaces, 1):
        print(f"      {i}. {iface}")

    if not interfaces:
        print("    ✗ No interfaces found!")
        print("    → Check Npcap installation")
        input("\nPress Enter to exit...")
        sys.exit(1)
except Exception as e:
    print(f"    ✗ Error getting interfaces: {e}")
    input("\nPress Enter to exit...")
    sys.exit(1)

# Check 5: Get your IP address
print("\n[5] Finding your IP address...")
try:
    import socket
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"    Hostname: {hostname}")
    print(f"    IP Address: {ip_address}")
    print(f"    → This PC should be: {ip_address}")
except Exception as e:
    print(f"    ? Could not get IP: {e}")

# Check 6: Test packet capture
print("\n[6] Testing packet capture (10 seconds)...")
print("    → Generate traffic now (ping this PC from another computer)")
print("    → Waiting for packets...")

captured_packets = []
packet_count = 0

def packet_callback(packet):
    global packet_count
    packet_count += 1

    # Get packet info
    if packet.haslayer(IP):
        src = packet[IP].src
        dst = packet[IP].dst
        protocol = "Unknown"

        if packet.haslayer(TCP):
            protocol = "TCP"
        elif packet.haslayer(UDP):
            protocol = "UDP"
        elif packet.haslayer(ICMP):
            protocol = "ICMP (ping)"

        print(f"    [{packet_count}] {protocol}: {src} → {dst}")

        captured_packets.append({
            'src': src,
            'dst': dst,
            'protocol': protocol
        })

try:
    # Capture for 10 seconds
    print()
    sniff(prn=packet_callback, timeout=10, store=False)

    print()
    if packet_count > 0:
        print(f"    ✓ Captured {packet_count} packet(s)")
        print("\n    PACKET CAPTURE IS WORKING! ✓")
    else:
        print("    ✗ No packets captured!")
        print("\n    PACKET CAPTURE IS NOT WORKING! ✗")
        print("\n    Possible causes:")
        print("    1. No traffic during test period")
        print("    2. Wrong network interface")
        print("    3. Npcap not working properly")
        print("    4. Firewall blocking")
        print("\n    Try:")
        print("    - Ping THIS PC from another computer during the test")
        print("    - Reinstall Npcap: https://npcap.com/")
        print("    - Check Windows Firewall settings")

except KeyboardInterrupt:
    print("\n    Test cancelled by user")
except Exception as e:
    print(f"\n    ✗ Error during packet capture: {e}")
    print(f"    Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 70)
print("DIAGNOSTIC SUMMARY")
print("=" * 70)

if packet_count > 0:
    print("\n✓ PACKET CAPTURE IS WORKING!")
    print("\nIf the IDS/IPS application still shows no packets:")
    print("  1. Check the console for error messages")
    print("  2. Verify you clicked 'Start Detection Mode'")
    print("  3. Check the 'Packets' counter in the UI")
    print("  4. Look for interface selection issues in logs")
else:
    print("\n✗ PACKET CAPTURE IS NOT WORKING!")
    print("\nTo fix:")
    print("  1. Reinstall Npcap: https://npcap.com/")
    print("     → Check 'WinPcap API-compatible Mode'")
    print("     → Restart computer after installation")
    print("  2. Verify Administrator privileges")
    print("  3. Check firewall isn't blocking")
    print("  4. Try pinging this PC from another computer")

print("\n" + "=" * 70)
input("\nPress Enter to exit...")

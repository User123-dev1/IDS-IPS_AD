#!/usr/bin/env python3
"""
Simple Packet Capture Test
Test if Scapy can capture packets on your system.

Run as Administrator:
    python test_capture_simple.py

While running, ping this PC from another computer.
"""

from scapy.all import sniff, IP

print("=" * 60)
print("Simple Packet Capture Test")
print("=" * 60)
print()
print("Starting packet capture test...")
print("Ping this PC from another computer NOW!")
print("Waiting 10 seconds...")
print()

counter = [0]

def packet_handler(pkt):
    """Handle each captured packet"""
    counter[0] += 1
    if pkt.haslayer(IP):
        print(f"Packet {counter[0]}: {pkt[IP].src} → {pkt[IP].dst}")

# Capture packets for 10 seconds
sniff(prn=packet_handler, timeout=10, store=False)

print()
print("=" * 60)
print(f"Captured {counter[0]} packets")
print("=" * 60)

if counter[0] > 0:
    print("✓ Packet capture WORKS!")
    print()
    print("Your system can capture packets correctly.")
    print("If the IDS/IPS app still doesn't work, the issue is in the application code.")
else:
    print("✗ Packet capture FAILED!")
    print()
    print("Possible causes:")
    print("  1. Not running as Administrator")
    print("  2. Npcap not installed or not working")
    print("  3. Npcap service not running")
    print("  4. No traffic on the network interface")
    print()
    print("Try:")
    print("  - Run as Administrator")
    print("  - Check: Get-Service npcap")
    print("  - Reinstall Npcap from https://npcap.com/")

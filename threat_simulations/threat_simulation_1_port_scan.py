#!/usr/bin/env python3
"""
Threat Simulation 1: Port Scanning Attack

This script simulates a port scanning attack to test IDS/IPS detection.
Expected Detection: Port scanning pattern (>100 packets/min to different ports)

⚠️ WARNING: Only use on networks you own or have permission to test!
"""

import socket
import time
import sys
from datetime import datetime

# Configuration
TARGET_IP = "192.168.1.50"  # ⚠️ CHANGE THIS to your IDS/IPS monitored system
PORT_RANGE = range(20, 1024)  # Scan ports 20-1024
SCAN_DELAY = 0.1  # Seconds between each port probe
TIMEOUT = 0.5  # Socket timeout

print("=" * 70)
print("THREAT SIMULATION 1: Port Scanning Attack")
print("=" * 70)
print(f"\nTarget IP: {TARGET_IP}")
print(f"Port Range: {PORT_RANGE.start}-{PORT_RANGE.stop}")
print(f"Scan Delay: {SCAN_DELAY}s")
print("\n⚠️  WARNING: This simulates a real port scan attack!")
print("    Only run on networks you own or have permission to test.")
print("\n" + "=" * 70)

# Confirmation
response = input("\nContinue with port scan simulation? (yes/no): ")
if response.lower() != 'yes':
    print("Simulation cancelled.")
    sys.exit(0)

print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting port scan...")
print("-" * 70)

open_ports = []
closed_ports = 0
filtered_ports = 0

start_time = time.time()

for port in PORT_RANGE:
    try:
        # Create TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)

        # Attempt connection
        result = sock.connect_ex((TARGET_IP, port))

        if result == 0:
            # Port is open
            open_ports.append(port)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Port {port:5d}: OPEN ✓")

            # Try to grab banner
            try:
                sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
                banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                if banner:
                    print(f"                  Banner: {banner[:100]}")
            except:
                pass
        else:
            closed_ports += 1
            # Only print every 100th closed port to avoid spam
            if closed_ports % 100 == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanned {closed_ports} ports...")

        sock.close()

    except socket.timeout:
        filtered_ports += 1
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user.")
        break
    except Exception as e:
        print(f"Error scanning port {port}: {e}")

    # Delay between probes
    time.sleep(SCAN_DELAY)

end_time = time.time()
duration = end_time - start_time

# Results
print("\n" + "=" * 70)
print("PORT SCAN RESULTS")
print("=" * 70)
print(f"Target:          {TARGET_IP}")
print(f"Ports Scanned:   {PORT_RANGE.start}-{PORT_RANGE.stop} ({len(PORT_RANGE)} ports)")
print(f"Duration:        {duration:.2f} seconds")
print(f"Scan Rate:       {len(PORT_RANGE)/duration:.2f} ports/second")
print(f"\nOpen Ports:      {len(open_ports)}")
print(f"Closed Ports:    {closed_ports}")
print(f"Filtered Ports:  {filtered_ports}")

if open_ports:
    print(f"\nOpen Ports List: {', '.join(map(str, open_ports[:20]))}")
    if len(open_ports) > 20:
        print(f"                 ... and {len(open_ports) - 20} more")

print("\n" + "=" * 70)
print("EXPECTED IDS/IPS DETECTION")
print("=" * 70)
print("✓ Rule-Based Detection:")
print("  - Port scanning pattern (>100 packets/min)")
print("  - Category: PORT_SCAN")
print("  - Severity: CRITICAL")
print("\n✓ ML Detection:")
print("  - High packet rate")
print("  - Multiple connection attempts")
print("  - No response on closed ports")
print("  - Threat Level: HIGH or CRITICAL")
print("\n✓ Baseline Anomaly:")
print("  - Unusual traffic pattern")
print("  - Multiple port connections from single source")
print("\n" + "=" * 70)
print("\nCheck the IDS/IPS 'Network Monitor' tab for detection alerts!")
print("=" * 70)

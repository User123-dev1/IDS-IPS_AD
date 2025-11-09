#!/usr/bin/env python3
"""
Threat Simulation 5: Backdoor & C2 Communication

This script simulates backdoor and Command & Control (C2) communication patterns:
- Persistent connections to unusual ports
- Beaconing (regular heartbeat)
- Data exfiltration patterns
- Reverse shell behavior
- C2 server communication

Expected Detection: Backdoor, Malware C2
⚠️ WARNING: Only use in authorized test environments!
"""

import socket
import time
import random
import sys
from datetime import datetime
import threading

# Configuration
C2_SERVER = "127.0.0.1"  # Simulated C2 server (use your IDS/IPS target)
C2_PORTS = [4444, 8080, 443, 31337]  # Common C2 ports
BEACON_INTERVAL = 10  # Seconds between beacons
BEACON_COUNT = 30  # Number of beacons to send
EXFIL_SIZE = 1024 * 50  # 50KB simulated data exfiltration


def print_header():
    """Print simulation header"""
    print("=" * 70)
    print("THREAT SIMULATION 5: Backdoor & C2 Communication")
    print("=" * 70)
    print(f"\nC2 Server:         {C2_SERVER}")
    print(f"C2 Ports:          {C2_PORTS}")
    print(f"Beacon Interval:   {BEACON_INTERVAL}s")
    print(f"Beacon Count:      {BEACON_COUNT}")
    print(f"Exfil Size:        {EXFIL_SIZE / 1024:.1f} KB")
    print(f"\n⚠️  WARNING: This simulates malware C2 communication!")
    print("    Mimics backdoor and remote access trojan (RAT) behavior.")
    print("    Only run on test networks with permission!")
    print("=" * 70)


def create_c2_connection(ip, port, persistent=True):
    """Create simulated C2 connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))

        # Send initial beacon (simulated)
        beacon_data = b"BEACON|" + str(random.randint(1000, 9999)).encode()
        sock.send(beacon_data)

        if persistent:
            # Keep connection alive
            sock.settimeout(None)
            return sock
        else:
            sock.close()
            return None

    except Exception as e:
        return None


def beaconing_simulation():
    """Simulate regular beaconing behavior (heartbeat to C2)"""
    print(f"\n🔄 Phase 1: Beaconing Simulation")
    print("-" * 70)
    print(f"Simulating regular heartbeat to C2 server...")
    print(f"This mimics malware 'check-in' behavior\n")

    beacon_port = random.choice(C2_PORTS)
    successful_beacons = 0

    for i in range(BEACON_COUNT):
        try:
            # Create short-lived connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((C2_SERVER, beacon_port))

            # Send beacon with timestamp
            beacon_msg = f"BEACON_{i}|{datetime.now().isoformat()}".encode()
            sock.send(beacon_msg)

            # Receive acknowledgment (simulated)
            try:
                sock.recv(128)
            except:
                pass

            sock.close()
            successful_beacons += 1

            if (i + 1) % 5 == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent {i+1}/{BEACON_COUNT} beacons")

            # Regular interval (characteristic of C2 beaconing)
            time.sleep(BEACON_INTERVAL)

        except Exception as e:
            pass

    print(f"✓ Beaconing complete: {successful_beacons}/{BEACON_COUNT} successful")
    return successful_beacons


def persistent_connection_simulation():
    """Simulate long-lived persistent connection"""
    print(f"\n🔗 Phase 2: Persistent Connection Simulation")
    print("-" * 70)
    print(f"Establishing long-lived connection to C2 server...")
    print(f"This mimics backdoor maintaining access\n")

    port = random.choice([4444, 31337, 8080])

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((C2_SERVER, port))

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to {C2_SERVER}:{port}")

        # Keep connection alive for extended period
        duration = 60  # 60 seconds
        start_time = time.time()
        keep_alive_count = 0

        while (time.time() - start_time) < duration:
            try:
                # Send keep-alive packet every 5 seconds
                sock.send(b"KEEPALIVE\n")
                keep_alive_count += 1

                if keep_alive_count % 6 == 0:
                    elapsed = int(time.time() - start_time)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection alive for {elapsed}s...")

                time.sleep(5)

            except:
                break

        sock.close()
        print(f"✓ Persistent connection maintained for {duration}s")
        return True

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def data_exfiltration_simulation():
    """Simulate data exfiltration over C2 channel"""
    print(f"\n📤 Phase 3: Data Exfiltration Simulation")
    print("-" * 70)
    print(f"Simulating data exfiltration ({EXFIL_SIZE / 1024:.1f} KB)...")
    print(f"This mimics stealing sensitive information\n")

    port = random.choice([443, 8080])  # HTTPS/HTTP ports for evasion

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((C2_SERVER, port))

        # Simulate exfiltrating data in chunks
        chunk_size = 1024  # 1KB chunks
        chunks = EXFIL_SIZE // chunk_size
        bytes_sent = 0

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting data transfer...")

        for i in range(chunks):
            # Create fake data
            fake_data = b'X' * chunk_size
            sock.send(fake_data)
            bytes_sent += chunk_size

            if (i + 1) % 10 == 0:
                print(f"  Transferred: {bytes_sent / 1024:.1f} KB / {EXFIL_SIZE / 1024:.1f} KB")

            time.sleep(0.1)  # Throttle to avoid flooding

        sock.close()
        print(f"✓ Exfiltration complete: {bytes_sent / 1024:.1f} KB sent")
        return bytes_sent

    except Exception as e:
        print(f"✗ Exfiltration failed: {e}")
        return 0


def reverse_shell_simulation():
    """Simulate reverse shell connection attempts"""
    print(f"\n💀 Phase 4: Reverse Shell Simulation")
    print("-" * 70)
    print(f"Simulating reverse shell connection...")
    print(f"This mimics remote command execution backdoor\n")

    shell_port = 4444  # Classic reverse shell port

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((C2_SERVER, shell_port))

        # Simulate shell commands being sent
        commands = [
            b"whoami\n",
            b"pwd\n",
            b"ls -la\n",
            b"uname -a\n",
            b"ifconfig\n",
            b"ps aux\n",
        ]

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Shell connected to {C2_SERVER}:{shell_port}")

        for cmd in commands:
            print(f"  Executing: {cmd.decode().strip()}")
            sock.send(cmd)
            time.sleep(1)

        sock.close()
        print(f"✓ Reverse shell simulation complete")
        return True

    except Exception as e:
        print(f"✗ Reverse shell failed: {e}")
        return False


def main():
    """Main backdoor simulation"""
    print_header()

    response = input("\nContinue with backdoor simulation? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Simulation cancelled.")
        return

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting backdoor simulation...")
    print("-" * 70)

    start_time = time.time()

    # Run simulations
    beacons = beaconing_simulation()
    persistent = persistent_connection_simulation()
    exfil_bytes = data_exfiltration_simulation()
    reverse_shell = reverse_shell_simulation()

    duration = time.time() - start_time

    # Summary
    print("\n" + "=" * 70)
    print("BACKDOOR SIMULATION RESULTS")
    print("=" * 70)
    print(f"C2 Server:           {C2_SERVER}")
    print(f"Beacons Sent:        {beacons}/{BEACON_COUNT}")
    print(f"Persistent Conn:     {'Yes' if persistent else 'No'}")
    print(f"Data Exfiltrated:    {exfil_bytes / 1024:.1f} KB")
    print(f"Reverse Shell:       {'Success' if reverse_shell else 'Failed'}")
    print(f"Total Duration:      {duration:.1f} seconds")

    print("\n" + "=" * 70)
    print("EXPECTED IDS/IPS DETECTION")
    print("=" * 70)
    print("✓ Rule-Based Detection:")
    print("  - Category: BACKDOOR / MALWARE_C2")
    print("  - Severity: CRITICAL")
    print("  - Patterns:")
    print("    • Regular beaconing (consistent intervals)")
    print("    • Connections to suspicious ports (4444, 31337)")
    print("    • Long-lived persistent connections")
    print("    • Unusual data transfer patterns")
    print("")
    print("✓ ML Detection:")
    print("  - Beaconing pattern (regular intervals)")
    print("  - Abnormal connection duration")
    print("  - Unusual data flow (exfiltration)")
    print("  - Reverse shell indicators")
    print("")
    print("✓ Behavioral Analysis:")
    print("  - C2 heartbeat detection")
    print("  - Persistent backdoor indicators")
    print("  - Command & Control communication")
    print("=" * 70)

    print("\nCheck the IDS/IPS 'Network Monitor' tab for detection alerts!")
    print("Expected alert: '🚨 CRITICAL: Backdoor/C2 communication detected'\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
Threat Simulation 2: Brute Force Attack

This script simulates a brute force attack against SSH/RDP/other services.
Expected Detection: Multiple failed authentication attempts (>20/min)

⚠️ WARNING: Only use on networks you own or have permission to test!
"""

import socket
import time
import sys
from datetime import datetime

# Configuration
TARGET_IP = "192.168.1.50"  # ⚠️ CHANGE THIS to your IDS/IPS monitored system
TARGET_PORT = 22  # SSH (22), RDP (3389), Telnet (23), HTTP (80)
ATTEMPTS = 50  # Number of authentication attempts
DELAY = 0.2  # Seconds between attempts

# Common passwords for simulation
PASSWORDS = [
    "admin", "password", "123456", "admin123", "root", "toor",
    "administrator", "letmein", "welcome", "changeme", "password123",
    "qwerty", "abc123", "111111", "monkey", "dragon", "master",
    "superman", "iloveyou", "trustno1", "football", "1234567",
    "welcome1", "admin@123", "root123", "password1", "test123"
]

print("=" * 70)
print("THREAT SIMULATION 2: Brute Force Attack")
print("=" * 70)
print(f"\nTarget IP:   {TARGET_IP}")
print(f"Target Port: {TARGET_PORT} ({'SSH' if TARGET_PORT == 22 else 'RDP' if TARGET_PORT == 3389 else 'Unknown'})")
print(f"Attempts:    {ATTEMPTS}")
print(f"Delay:       {DELAY}s between attempts")
print("\n⚠️  WARNING: This simulates a real brute force attack!")
print("    Only run on networks you own or have permission to test.")
print("\n" + "=" * 70)

# Confirmation
response = input("\nContinue with brute force simulation? (yes/no): ")
if response.lower() != 'yes':
    print("Simulation cancelled.")
    sys.exit(0)

print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting brute force attack simulation...")
print("-" * 70)

start_time = time.time()
attempt_count = 0
connection_attempts = 0
successful_connections = 0

# Use cycle through password list
password_index = 0

for attempt in range(1, ATTEMPTS + 1):
    password = PASSWORDS[password_index % len(PASSWORDS)]
    password_index += 1

    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        # Attempt connection (simulating authentication attempt)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Attempt {attempt:3d}/{ATTEMPTS}: "
              f"admin:{password:<15s} -> ", end="")

        result = sock.connect_ex((TARGET_IP, TARGET_PORT))

        if result == 0:
            connection_attempts += 1

            # For SSH, try to send initial data (simulates auth attempt)
            if TARGET_PORT == 22:
                try:
                    # Read SSH banner
                    banner = sock.recv(1024)
                    print(f"Connected [SSH banner received] ✗ FAILED")

                    # Send fake SSH version
                    sock.send(b"SSH-2.0-OpenSSH_7.4\r\n")
                    time.sleep(0.1)

                except Exception as e:
                    print(f"Connected but error: {e} ✗ FAILED")
            else:
                # For other services, just connect and disconnect
                print(f"Connected ✗ FAILED (auth failed)")

        else:
            print(f"Connection refused ✗ FAILED")

        sock.close()
        attempt_count += 1

    except socket.timeout:
        print(f"Timeout ✗ FAILED")
        attempt_count += 1
    except ConnectionRefusedError:
        print(f"Connection refused ✗ FAILED")
        attempt_count += 1
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        break
    except Exception as e:
        print(f"Error: {e} ✗ FAILED")
        attempt_count += 1

    # Delay between attempts
    time.sleep(DELAY)

    # Show progress every 10 attempts
    if attempt % 10 == 0:
        elapsed = time.time() - start_time
        rate = attempt / elapsed
        print(f"        Progress: {attempt}/{ATTEMPTS} attempts ({rate:.1f} attempts/sec)")

end_time = time.time()
duration = end_time - start_time

# Results
print("\n" + "=" * 70)
print("BRUTE FORCE ATTACK RESULTS")
print("=" * 70)
print(f"Target:             {TARGET_IP}:{TARGET_PORT}")
print(f"Total Attempts:     {attempt_count}")
print(f"Duration:           {duration:.2f} seconds")
print(f"Attack Rate:        {attempt_count/duration:.2f} attempts/second")
print(f"Connections Made:   {connection_attempts}")
print(f"Successful Logins:  {successful_connections} (simulated - all should fail)")

print("\n" + "=" * 70)
print("EXPECTED IDS/IPS DETECTION")
print("=" * 70)
print("✓ Rule-Based Detection:")
print("  - Brute force attack pattern (>20 attempts/min)")
print("  - Category: BRUTE_FORCE")
print("  - Severity: CRITICAL")
print(f"  - Target Port: {TARGET_PORT}")
print("\n✓ ML Detection:")
print("  - High connection rate to single port")
print("  - Multiple failed authentication patterns")
print("  - Short-lived connections")
print("  - Threat Level: HIGH or CRITICAL")
print("\n✓ Baseline Anomaly:")
print("  - Unusual authentication activity")
print("  - High frequency connections")
print("\n" + "=" * 70)
print("\nCheck the IDS/IPS 'Network Monitor' tab for detection alerts!")
print("Expected alert: '🚨 Potential brute force attack'")
print("=" * 70)

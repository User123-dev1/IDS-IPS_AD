#!/usr/bin/env python3
"""
Threat Simulation 10: Generic Malicious Traffic

This script simulates generic malicious traffic patterns:
- Suspicious connections
- Unusual protocols
- Abnormal traffic patterns
- Mixed attack behaviors
- General network anomalies

Expected Detection: Generic, Suspicious Activity
⚠️ WARNING: Only use in authorized test environments!
"""

import socket
import time
import random
import sys
from datetime import datetime

# Configuration
TARGET_IP = "127.0.0.1"
RANDOM_PORTS = list(range(1024, 65535, 1000))
DURATION = 60  # seconds


def print_header():
    """Print simulation header"""
    print("=" * 70)
    print("THREAT SIMULATION 10: Generic Malicious Traffic")
    print("=" * 70)
    print(f"\nTarget IP:         {TARGET_IP}")
    print(f"Duration:          {DURATION}s")
    print(f"Port Range:        Random high ports")
    print(f"\n⚠️  WARNING: This simulates generic malicious behavior!")
    print("    Mix of suspicious activities and anomalous traffic.")
    print("    Only run on test networks with permission!")
    print("=" * 70)


def suspicious_connections():
    """Generate suspicious connection patterns"""
    print(f"\n🔗 Suspicious Connection Patterns")
    print("-" * 70)

    connections = 0

    # Connect to unusual high ports
    for _ in range(20):
        port = random.choice(RANDOM_PORTS)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((TARGET_IP, port))
            sock.send(b'SUSPICIOUS_DATA\n')
            sock.close()
            connections += 1
        except:
            pass
        time.sleep(0.5)

    print(f"  Generated {connections} suspicious connections")
    return connections


def unusual_traffic_patterns():
    """Generate unusual traffic patterns"""
    print(f"\n📊 Unusual Traffic Patterns")
    print("-" * 70)

    patterns = 0

    # Burst traffic
    print(f"  Generating burst traffic...")
    for i in range(10):
        for port in [80, 443, 8080]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                sock.connect((TARGET_IP, port))
                sock.send(b'X' * random.randint(100, 1000))
                sock.close()
                patterns += 1
            except:
                pass
        time.sleep(0.1)

    # Slow traffic
    print(f"  Generating slow/irregular traffic...")
    for _ in range(5):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((TARGET_IP, 80))

            # Send data slowly
            for _ in range(10):
                sock.send(b'A')
                time.sleep(0.5)

            sock.close()
            patterns += 1
        except:
            pass

    print(f"  Generated {patterns} unusual traffic patterns")
    return patterns


def abnormal_packet_sizes():
    """Send packets with abnormal sizes"""
    print(f"\n📦 Abnormal Packet Sizes")
    print("-" * 70)

    sent = 0

    abnormal_sizes = [1, 16000, 32000, 64000]  # Very small and very large

    for size in abnormal_sizes:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((TARGET_IP, 80))

            data = b'A' * min(size, 65000)  # Cap at socket limit
            sock.send(data)
            sock.close()
            sent += 1

            print(f"  Sent {size} byte packet")
            time.sleep(0.5)
        except:
            pass

    print(f"  Sent {sent} abnormal-sized packets")
    return sent


def mixed_protocol_abuse():
    """Abuse multiple protocols"""
    print(f"\n🔀 Mixed Protocol Abuse")
    print("-" * 70)

    abuse_count = 0

    # HTTP abuse
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((TARGET_IP, 80))
        sock.send(b"GET " + b"/" * 1000 + b" HTTP/1.1\r\n\r\n")
        sock.close()
        abuse_count += 1
        print(f"  HTTP protocol abuse")
        time.sleep(0.5)
    except:
        pass

    # Random protocol data
    protocols = [21, 22, 23, 25, 110, 143, 443]
    for port in protocols:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((TARGET_IP, port))
            sock.send(b'\x00\xFF\xAA\x55' * 50)  # Random binary data
            sock.close()
            abuse_count += 1
        except:
            pass
        time.sleep(0.3)

    print(f"  Protocol abuse attempts: {abuse_count}")
    return abuse_count


def suspicious_data_patterns():
    """Send suspicious data patterns"""
    print(f"\n🎯 Suspicious Data Patterns")
    print("-" * 70)

    patterns_sent = 0

    suspicious_data = [
        b'\x00' * 500,  # All nulls
        b'\xFF' * 500,  # All 0xFF
        b'\xDE\xAD\xBE\xEF' * 125,  # Repeating pattern
        b'AAAAAAAA' * 125,  # Repeating ASCII
        bytes(range(256)) * 4,  # Sequential bytes
    ]

    for data in suspicious_data:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((TARGET_IP, 80))
            sock.send(data)
            sock.close()
            patterns_sent += 1
            time.sleep(0.3)
        except:
            pass

    print(f"  Suspicious patterns sent: {patterns_sent}")
    return patterns_sent


def random_malicious_behavior():
    """Generate random malicious-looking behavior"""
    print(f"\n🎲 Random Malicious Behavior")
    print("-" * 70)

    behaviors = 0

    for _ in range(15):
        # Random port
        port = random.choice([21, 22, 23, 25, 80, 443, 445, 3389, 8080] + RANDOM_PORTS[:10])

        # Random action
        action = random.choice([
            'rapid_connect',
            'send_random',
            'partial_handshake',
            'connection_flood'
        ])

        try:
            if action == 'rapid_connect':
                for _ in range(5):
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    sock.connect((TARGET_IP, port))
                    sock.close()

            elif action == 'send_random':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((TARGET_IP, port))
                sock.send(bytes([random.randint(0, 255) for _ in range(random.randint(50, 500))]))
                sock.close()

            elif action == 'partial_handshake':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                sock.connect((TARGET_IP, port))
                # Don't close - let it timeout

            elif action == 'connection_flood':
                for _ in range(3):
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    sock.connect((TARGET_IP, port))
                    sock.send(b'FLOOD')
                    sock.close()

            behaviors += 1

        except:
            pass

        time.sleep(0.5)

    print(f"  Random behaviors executed: {behaviors}")
    return behaviors


def main():
    """Main generic attack simulation"""
    print_header()

    response = input("\nContinue with generic attack simulation? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Simulation cancelled.")
        return

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting generic malicious traffic...")
    print("-" * 70)

    start_time = time.time()
    total_actions = 0

    # Run all generic attacks
    total_actions += suspicious_connections()
    total_actions += unusual_traffic_patterns()
    total_actions += abnormal_packet_sizes()
    total_actions += mixed_protocol_abuse()
    total_actions += suspicious_data_patterns()
    total_actions += random_malicious_behavior()

    duration = time.time() - start_time

    # Summary
    print("\n" + "=" * 70)
    print("GENERIC ATTACK SIMULATION RESULTS")
    print("=" * 70)
    print(f"Target:              {TARGET_IP}")
    print(f"Total Actions:       {total_actions}")
    print(f"Attack Types:        6")
    print("  - Suspicious Connections")
    print("  - Unusual Traffic Patterns")
    print("  - Abnormal Packet Sizes")
    print("  - Protocol Abuse")
    print("  - Suspicious Data Patterns")
    print("  - Random Malicious Behavior")
    print(f"Duration:            {duration:.1f}s")
    print(f"Action Rate:         {total_actions / duration:.1f} actions/s")

    print("\n" + "=" * 70)
    print("EXPECTED IDS/IPS DETECTION")
    print("=" * 70)
    print("✓ Rule-Based Detection:")
    print("  - Category: GENERIC / SUSPICIOUS_ACTIVITY")
    print("  - Severity: MEDIUM-HIGH")
    print("  - Patterns:")
    print("    • Unusual connection patterns")
    print("    • Abnormal packet sizes")
    print("    • Protocol violations")
    print("    • Suspicious data patterns")
    print("    • Mixed malicious behaviors")
    print("")
    print("✓ ML Detection:")
    print("  - Anomalous traffic patterns")
    print("  - Unusual data structures")
    print("  - Behavioral anomalies")
    print("  - Statistical outliers")
    print("")
    print("✓ Behavioral Analysis:")
    print("  - General malicious intent")
    print("  - Suspicious network activity")
    print("  - Abnormal communication patterns")
    print("=" * 70)

    print("\nCheck the IDS/IPS 'Network Monitor' tab for detection alerts!")
    print("Expected alert: '⚠️ Generic suspicious activity detected'\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

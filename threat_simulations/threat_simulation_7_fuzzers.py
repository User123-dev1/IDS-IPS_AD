#!/usr/bin/env python3
"""
Threat Simulation 7: Fuzzing & Malformed Packets

This script simulates fuzzing activities:
- Malformed HTTP requests
- Invalid protocol data
- Random payloads
- Format string attacks
- Edge case inputs
- Crash attempts

Expected Detection: Fuzzers, Malformed Traffic
⚠️ WARNING: Only use in authorized test environments!
"""

import socket
import time
import random
import sys
from datetime import datetime

# Configuration
TARGET_IP = "127.0.0.1"
FUZZ_PORTS = [80, 443, 21, 22, 23]
FUZZ_COUNT = 100
DELAY = 0.1


def print_header():
    """Print simulation header"""
    print("=" * 70)
    print("THREAT SIMULATION 7: Fuzzing & Malformed Packets")
    print("=" * 70)
    print(f"\nTarget IP:         {TARGET_IP}")
    print(f"Fuzz Ports:        {FUZZ_PORTS}")
    print(f"Fuzz Count:        {FUZZ_COUNT}")
    print(f"Delay:             {DELAY}s")
    print(f"\n⚠️  WARNING: This sends malformed packets!")
    print("    Mimics fuzzing tools like AFL, Peach, Sulley.")
    print("    May cause service instability - test environment only!")
    print("=" * 70)


def generate_random_bytes(length):
    """Generate random bytes for fuzzing"""
    return bytes([random.randint(0, 255) for _ in range(length)])


def malformed_http_fuzzing(ip, port=80):
    """Send malformed HTTP requests"""
    print(f"\n🔨 Malformed HTTP Fuzzing")
    print("-" * 70)

    malformed_requests = [
        b"GET / HTTP/99.99\r\n\r\n",  # Invalid HTTP version
        b"XXXXXX / HTTP/1.1\r\n\r\n",  # Invalid method
        b"GET " + b"A" * 10000 + b" HTTP/1.1\r\n\r\n",  # Overlong URL
        b"GET / HTTP/1.1\r\n" + b"X" * 5000 + b"\r\n\r\n",  # Overlong header
        b"\x00\x00\x00\x00GET / HTTP/1.1\r\n\r\n",  # Null bytes
        b"GET /%00%00%00 HTTP/1.1\r\n\r\n",  # Null encoding
        b"GET / HTTP/1.1\r\nHost: \x7f\x00\x00\x01\r\n\r\n",  # Binary in header
        b"GET /../../../etc/passwd HTTP/",  # Incomplete request
    ]

    sent = 0
    for req in malformed_requests:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, port))
            sock.send(req)
            sock.close()
            sent += 1
            time.sleep(DELAY)
        except:
            pass

    print(f"  Sent {sent} malformed HTTP requests")
    return sent


def random_payload_fuzzing(ip, port):
    """Send completely random data"""
    print(f"\n🎲 Random Payload Fuzzing")
    print("-" * 70)

    sent = 0
    sizes = [16, 64, 256, 512, 1024, 2048]

    for size in sizes:
        for _ in range(5):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((ip, port))

                # Send random bytes
                random_data = generate_random_bytes(size)
                sock.send(random_data)
                sock.close()
                sent += 1

                time.sleep(DELAY)
            except:
                pass

    print(f"  Sent {sent} random payloads ({min(sizes)}-{max(sizes)} bytes)")
    return sent


def format_string_fuzzing(ip, port=80):
    """Send format string attack patterns"""
    print(f"\n📝 Format String Fuzzing")
    print("-" * 70)

    format_strings = [
        b"%s%s%s%s%s%s%s%s",
        b"%x%x%x%x%x%x%x%x",
        b"%n%n%n%n%n%n",
        b"AAAA" + b"%08x." * 100,
        b"%p" * 50,
        b"%" + b"A" * 1000 + b"x",
    ]

    sent = 0
    for fs in format_strings:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, port))

            request = b"GET /?input=" + fs + b" HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n"
            sock.send(request)
            sock.close()
            sent += 1

            time.sleep(DELAY)
        except:
            pass

    print(f"  Sent {sent} format string patterns")
    return sent


def edge_case_fuzzing(ip, port=80):
    """Send edge case inputs"""
    print(f"\n🎯 Edge Case Fuzzing")
    print("-" * 70)

    edge_cases = [
        b"-1",
        b"0",
        b"2147483647",  # Max int32
        b"-2147483648",  # Min int32
        b"99999999999999999999",  # Overflow
        b"0x7fffffff",
        b"\xff" * 100,  # All 0xFF
        b"\x00" * 100,  # All nulls
        b"NaN",
        b"Infinity",
        b"-Infinity",
    ]

    sent = 0
    for case in edge_cases:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, port))

            request = b"GET /?val=" + case + b" HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n"
            sock.send(request)
            sock.close()
            sent += 1

            time.sleep(DELAY)
        except:
            pass

    print(f"  Sent {sent} edge case inputs")
    return sent


def protocol_violation_fuzzing(ip):
    """Send protocol violations"""
    print(f"\n⚠️  Protocol Violation Fuzzing")
    print("-" * 70)

    violations = [
        # FTP violations
        {"port": 21, "data": b"USER " + b"A" * 5000 + b"\r\n"},
        {"port": 21, "data": b"XXXX INVALID COMMAND\r\n"},

        # SSH violations
        {"port": 22, "data": b"SSH-99.99-OpenSSH_Invalid\r\n"},
        {"port": 22, "data": b"\x00" * 100},

        # HTTP violations
        {"port": 80, "data": b"HTTP/1.1 200 OK\r\n\r\n"},  # Client sending response
        {"port": 80, "data": b"\r\n\r\n"},  # Empty request
    ]

    sent = 0
    for violation in violations:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, violation['port']))
            sock.send(violation['data'])
            sock.close()
            sent += 1

            time.sleep(DELAY)
        except:
            pass

    print(f"  Sent {sent} protocol violations")
    return sent


def crash_attempt_fuzzing(ip, port=80):
    """Attempt to crash service with known patterns"""
    print(f"\n💥 Crash Attempt Fuzzing")
    print("-" * 70)

    crash_patterns = [
        b"A" * 10000,  # Long input
        b"%n" * 1000,  # Format string spam
        b"\x90" * 2000,  # NOP sled
        b"\xff\xfe\xfd\xfc" * 500,  # Invalid UTF-8
        b"../../../" * 100,  # Path traversal spam
        generate_random_bytes(8192),  # Large random
    ]

    sent = 0
    for pattern in crash_patterns:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, port))
            sock.send(pattern)
            sock.close()
            sent += 1

            time.sleep(DELAY)
        except:
            pass

    print(f"  Sent {sent} crash attempt patterns")
    return sent


def main():
    """Main fuzzing simulation"""
    print_header()

    response = input("\nContinue with fuzzing simulation? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Simulation cancelled.")
        return

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting fuzzing attacks...")
    print("-" * 70)

    total_sent = 0

    # Run all fuzzing simulations
    total_sent += malformed_http_fuzzing(TARGET_IP)
    total_sent += random_payload_fuzzing(TARGET_IP, 80)
    total_sent += format_string_fuzzing(TARGET_IP)
    total_sent += edge_case_fuzzing(TARGET_IP)
    total_sent += protocol_violation_fuzzing(TARGET_IP)
    total_sent += crash_attempt_fuzzing(TARGET_IP)

    # Summary
    print("\n" + "=" * 70)
    print("FUZZING SIMULATION RESULTS")
    print("=" * 70)
    print(f"Target:              {TARGET_IP}")
    print(f"Total Fuzz Inputs:   {total_sent}")
    print(f"Fuzzing Types:       6")
    print("  - Malformed HTTP")
    print("  - Random Payloads")
    print("  - Format Strings")
    print("  - Edge Cases")
    print("  - Protocol Violations")
    print("  - Crash Attempts")

    print("\n" + "=" * 70)
    print("EXPECTED IDS/IPS DETECTION")
    print("=" * 70)
    print("✓ Rule-Based Detection:")
    print("  - Category: FUZZERS / MALFORMED_TRAFFIC")
    print("  - Severity: HIGH")
    print("  - Patterns:")
    print("    • Malformed HTTP requests")
    print("    • Invalid protocol data")
    print("    • Format string patterns (%n, %s, %x)")
    print("    • Unusual binary data")
    print("    • Protocol violations")
    print("")
    print("✓ ML Detection:")
    print("  - Abnormal packet structures")
    print("  - Random/chaotic data patterns")
    print("  - High volume of malformed requests")
    print("")
    print("✓ Behavioral Analysis:")
    print("  - Fuzzing tool signatures")
    print("  - Systematic input manipulation")
    print("  - Crash attempt patterns")
    print("=" * 70)

    print("\nCheck the IDS/IPS 'Network Monitor' tab for detection alerts!")
    print("Expected alert: '⚠️ Fuzzing/Malformed traffic detected'\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

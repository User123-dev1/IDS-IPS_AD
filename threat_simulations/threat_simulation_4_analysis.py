#!/usr/bin/env python3
"""
Threat Simulation 4: Analysis & Network Fingerprinting

This script simulates network analysis and fingerprinting activities:
- Service version detection
- OS fingerprinting
- Protocol analysis
- Banner grabbing
- HTTP method enumeration

Expected Detection: Analysis, Reconnaissance
⚠️ WARNING: Only use in authorized test environments!
"""

import socket
import time
import sys
from datetime import datetime

# Configuration
TARGET_IP = "127.0.0.1"  # Change to your IDS/IPS monitored target
ANALYSIS_PORTS = [21, 22, 23, 25, 80, 110, 143, 443, 3306, 5432, 8080]
DELAY_BETWEEN_PROBES = 0.5  # seconds


def print_header():
    """Print simulation header"""
    print("=" * 70)
    print("THREAT SIMULATION 4: Analysis & Network Fingerprinting")
    print("=" * 70)
    print(f"\nTarget IP:         {TARGET_IP}")
    print(f"Ports to analyze:  {len(ANALYSIS_PORTS)}")
    print(f"Probe delay:       {DELAY_BETWEEN_PROBES}s")
    print(f"\n⚠️  WARNING: This simulates network reconnaissance!")
    print("    Mimics attacker gathering intelligence about the target.")
    print("    Only run on test networks with permission!")
    print("=" * 70)


def banner_grab(ip, port, timeout=2):
    """Attempt to grab service banner"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))

        # Send various probes
        probes = [
            b"GET / HTTP/1.0\r\n\r\n",  # HTTP
            b"HELP\r\n",                 # Generic
            b"USER anonymous\r\n",       # FTP
            b"\r\n",                     # Generic newline
        ]

        for probe in probes:
            try:
                sock.send(probe)
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                if banner:
                    return banner[:200]  # Return first 200 chars
            except:
                continue

        sock.close()
        return None

    except:
        return None


def http_method_enumeration(ip, port=80):
    """Enumerate HTTP methods (OPTIONS, TRACE, etc.)"""
    methods = ['OPTIONS', 'TRACE', 'PUT', 'DELETE', 'CONNECT', 'PROPFIND']
    results = []

    for method in methods:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, port))

            request = f"{method} / HTTP/1.1\r\nHost: {ip}\r\n\r\n"
            sock.send(request.encode())
            response = sock.recv(1024).decode('utf-8', errors='ignore')

            if '200' in response or '405' in response or '501' in response:
                results.append(method)

            sock.close()
            time.sleep(0.1)

        except:
            pass

    return results


def tcp_fingerprinting(ip, port):
    """Perform TCP fingerprinting (mimics Nmap, Xprobe2)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)

        # Set unusual TCP options (fingerprinting technique)
        # This creates unusual traffic patterns
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        start = time.time()
        result = sock.connect_ex((ip, port))
        latency = (time.time() - start) * 1000  # ms

        sock.close()

        return {
            'open': result == 0,
            'latency': f"{latency:.2f}ms"
        }

    except:
        return {'open': False, 'latency': 'N/A'}


def main():
    """Main analysis simulation"""
    print_header()

    response = input("\nContinue with analysis simulation? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Simulation cancelled.")
        return

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting network analysis...")
    print("-" * 70)

    total_probes = 0
    open_services = []

    # Phase 1: Service Detection
    print(f"\n📡 Phase 1: Service Detection & Banner Grabbing")
    print("-" * 70)

    for port in ANALYSIS_PORTS:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Probing port {port}...", end='')

        # TCP fingerprinting
        fingerprint = tcp_fingerprinting(TARGET_IP, port)
        total_probes += 1

        if fingerprint['open']:
            print(f" OPEN (latency: {fingerprint['latency']})")
            open_services.append(port)

            # Banner grabbing
            print(f"    └─ Grabbing banner...", end='')
            banner = banner_grab(TARGET_IP, port)
            total_probes += 1

            if banner:
                print(f" Got {len(banner)} bytes")
                print(f"       Banner: {banner[:60]}...")
            else:
                print(" No banner")
        else:
            print(" closed/filtered")

        time.sleep(DELAY_BETWEEN_PROBES)

    # Phase 2: HTTP Analysis (if HTTP port is open)
    if 80 in open_services or 8080 in open_services:
        print(f"\n🌐 Phase 2: HTTP Method Enumeration")
        print("-" * 70)

        http_port = 80 if 80 in open_services else 8080
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Enumerating HTTP methods on port {http_port}...")

        methods = http_method_enumeration(TARGET_IP, http_port)
        total_probes += len(['OPTIONS', 'TRACE', 'PUT', 'DELETE', 'CONNECT', 'PROPFIND'])

        if methods:
            print(f"    Allowed methods: {', '.join(methods)}")
        else:
            print(f"    Could not enumerate methods")

    # Phase 3: Protocol-Specific Probes
    print(f"\n🔍 Phase 3: Protocol-Specific Analysis")
    print("-" * 70)

    protocol_map = {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        80: "HTTP",
        110: "POP3",
        143: "IMAP",
        443: "HTTPS",
        3306: "MySQL",
        5432: "PostgreSQL",
    }

    for port in open_services:
        if port in protocol_map:
            protocol = protocol_map[port]
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Analyzing {protocol} on port {port}...")

            # Send protocol-specific probes
            banner = banner_grab(TARGET_IP, port)
            total_probes += 1

            time.sleep(DELAY_BETWEEN_PROBES)

    # Summary
    print("\n" + "=" * 70)
    print("ANALYSIS SIMULATION RESULTS")
    print("=" * 70)
    print(f"Target:              {TARGET_IP}")
    print(f"Total Probes:        {total_probes}")
    print(f"Open Services:       {len(open_services)}")
    print(f"Services Found:      {open_services}")
    print(f"Duration:            {len(ANALYSIS_PORTS) * DELAY_BETWEEN_PROBES:.1f} seconds")

    print("\n" + "=" * 70)
    print("EXPECTED IDS/IPS DETECTION")
    print("=" * 70)
    print("✓ Rule-Based Detection:")
    print("  - Category: ANALYSIS / RECONNAISSANCE")
    print("  - Severity: MEDIUM-HIGH")
    print("  - Pattern: Service enumeration, banner grabbing")
    print("")
    print("✓ ML Detection:")
    print("  - Unusual connection patterns")
    print("  - Multiple service probes")
    print("  - Fingerprinting behavior")
    print("")
    print("✓ Behavioral Analysis:")
    print("  - Sequential port probing")
    print("  - Protocol-specific queries")
    print("  - Information gathering")
    print("=" * 70)

    print("\nCheck the IDS/IPS 'Network Monitor' tab for detection alerts!")
    print("Expected alert: '⚠️ Analysis/Reconnaissance activity detected'\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

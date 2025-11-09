#!/usr/bin/env python3
"""
Threat Simulation 9: Worm Propagation

This script simulates worm-like propagation behavior:
- Network scanning for vulnerable hosts
- Self-replication attempts
- Mass exploitation
- Lateral movement
- Rapid spreading patterns

Expected Detection: Worms, Mass Scanning
⚠️ WARNING: Only use in authorized test environments!
"""

import socket
import time
import random
import sys
from datetime import datetime
import threading

# Configuration
NETWORK_SUBNET = "127.0.0"  # Change to your test subnet
SCAN_RANGE = range(1, 255)  # IPs to scan
WORM_PORTS = [445, 139, 22, 80, 3389]  # Common worm targets
MAX_THREADS = 20
PROPAGATION_ATTEMPTS = 50


def print_header():
    """Print simulation header"""
    print("=" * 70)
    print("THREAT SIMULATION 9: Worm Propagation")
    print("=" * 70)
    print(f"\nTarget Subnet:     {NETWORK_SUBNET}.0/24")
    print(f"Scan Range:        {len(SCAN_RANGE)} hosts")
    print(f"Worm Ports:        {WORM_PORTS}")
    print(f"Max Threads:       {MAX_THREADS}")
    print(f"Propagation:       {PROPAGATION_ATTEMPTS} attempts")
    print(f"\n⚠️  WARNING: This simulates worm propagation!")
    print("    Mimics self-replicating malware behavior.")
    print("    High network activity - test environment only!")
    print("=" * 70)


def rapid_network_scan(subnet, host_id):
    """Scan a single host (used by worm to find targets)"""
    ip = f"{subnet}.{host_id}"
    vulnerable = False

    for port in WORM_PORTS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((ip, port))
            sock.close()

            if result == 0:
                vulnerable = True
                break

        except:
            pass

    return {'ip': ip, 'vulnerable': vulnerable}


def mass_scanning_simulation():
    """Simulate mass scanning (worm looking for targets)"""
    print(f"\n🔍 Phase 1: Mass Network Scanning")
    print("-" * 70)
    print(f"Scanning {len(SCAN_RANGE)} hosts across {len(WORM_PORTS)} ports...")
    print(f"This mimics worm reconnaissance for vulnerable systems\n")

    targets_found = []
    scanned = 0

    # Simulate rapid concurrent scanning
    def scan_worker(host_id):
        return rapid_network_scan(NETWORK_SUBNET, host_id)

    # Use threading to simulate worm's concurrent scanning
    from concurrent.futures import ThreadPoolExecutor, as_completed

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(scan_worker, host_id): host_id
                   for host_id in list(SCAN_RANGE)[:PROPAGATION_ATTEMPTS]}

        for future in as_completed(futures):
            result = future.result()
            scanned += 1

            if result['vulnerable']:
                targets_found.append(result['ip'])

            if scanned % 10 == 0:
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] Scanned: {scanned}/{PROPAGATION_ATTEMPTS} hosts")

    elapsed = time.time() - start_time
    scan_rate = scanned / elapsed

    print(f"\n✓ Scan complete:")
    print(f"  Hosts scanned:     {scanned}")
    print(f"  Scan rate:         {scan_rate:.1f} hosts/second")
    print(f"  Targets found:     {len(targets_found)}")
    print(f"  Duration:          {elapsed:.1f}s")

    return targets_found


def exploitation_attempts(targets):
    """Simulate worm trying to exploit vulnerable hosts"""
    print(f"\n💥 Phase 2: Mass Exploitation")
    print("-" * 70)
    print(f"Attempting to exploit {min(len(targets), 10)} vulnerable targets...")
    print(f"This mimics worm spreading to new hosts\n")

    exploit_payloads = [
        b'\x00\x00\x00\x2f\xff' + b'SMB' + b'\x00' * 100,  # SMB exploit
        b'SSH-2.0-Exploit\r\n',  # SSH exploit
        b'GET /exploit HTTP/1.0\r\n\r\n',  # HTTP exploit
    ]

    successful_exploits = 0

    for target_ip in targets[:10]:  # Limit to avoid overwhelming
        for port in WORM_PORTS:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((target_ip, port))

                # Send exploit payload
                payload = random.choice(exploit_payloads)
                sock.send(payload)
                sock.close()

                successful_exploits += 1
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] Exploit sent to {target_ip}:{port}")

                time.sleep(0.1)
                break  # Move to next target

            except:
                pass

    print(f"\n✓ Exploitation attempts: {successful_exploits}")
    return successful_exploits


def payload_delivery_simulation(target_count):
    """Simulate worm payload delivery and execution"""
    print(f"\n📦 Phase 3: Payload Delivery")
    print("-" * 70)
    print(f"Delivering worm payload to compromised hosts...")
    print(f"This mimics worm self-replication\n")

    # Simulated worm payload (NOT real malware)
    worm_payload = b'\x4d\x5a\x90\x00' + b'\x00' * 200  # MZ header simulation

    delivered = 0

    for i in range(min(target_count, 5)):
        target_ip = f"{NETWORK_SUBNET}.{random.randint(1, 254)}"

        try:
            # Simulate payload transfer
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((target_ip, random.choice([445, 139, 80])))

            # Send worm binary
            sock.send(worm_payload)
            sock.close()

            delivered += 1
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Payload delivered to {target_ip}")

            time.sleep(0.5)

        except:
            pass

    print(f"\n✓ Payloads delivered: {delivered}")
    return delivered


def lateral_movement_simulation():
    """Simulate lateral movement across network"""
    print(f"\n↔️  Phase 4: Lateral Movement")
    print("-" * 70)
    print(f"Attempting to spread across network segments...")
    print(f"This mimics worm moving between systems\n")

    # Simulate connections to multiple hosts
    movement_attempts = 10
    successful_moves = 0

    for i in range(movement_attempts):
        source_ip = f"{NETWORK_SUBNET}.{random.randint(1, 254)}"
        dest_ip = f"{NETWORK_SUBNET}.{random.randint(1, 254)}"
        port = random.choice([445, 139, 22, 3389])

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((dest_ip, port))

            # Simulate credential use or exploit
            sock.send(b'WORM_LATERAL_MOVE\n')
            sock.close()

            successful_moves += 1
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Moved: {source_ip} → {dest_ip}:{port}")

            time.sleep(0.3)

        except:
            pass

    print(f"\n✓ Lateral movements: {successful_moves}/{movement_attempts}")
    return successful_moves


def rapid_replication_simulation():
    """Simulate rapid self-replication"""
    print(f"\n🔄 Phase 5: Rapid Replication")
    print("-" * 70)
    print(f"Simulating exponential worm replication...")
    print(f"This mimics worm creating copies of itself\n")

    # Simulate replication to multiple hosts simultaneously
    replication_threads = []

    def replicate_to_host(target_ip):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((target_ip, 445))
            sock.send(b'WORM_COPY\n')
            sock.close()
            return True
        except:
            return False

    # Launch multiple replication attempts concurrently
    replicated = 0
    for i in range(15):
        target_ip = f"{NETWORK_SUBNET}.{random.randint(1, 254)}"
        if replicate_to_host(target_ip):
            replicated += 1
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Replicated to {target_ip}")

        time.sleep(0.2)

    print(f"\n✓ Replication events: {replicated}")
    return replicated


def main():
    """Main worm simulation"""
    print_header()

    response = input("\nContinue with worm simulation? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Simulation cancelled.")
        return

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting worm propagation simulation...")
    print("-" * 70)

    start_time = time.time()

    # Run all worm phases
    targets = mass_scanning_simulation()
    exploits = exploitation_attempts(targets if targets else [f"{NETWORK_SUBNET}.1"])
    payloads = payload_delivery_simulation(max(exploits, 1))
    lateral = lateral_movement_simulation()
    replication = rapid_replication_simulation()

    total_time = time.time() - start_time

    # Summary
    print("\n" + "=" * 70)
    print("WORM PROPAGATION SIMULATION RESULTS")
    print("=" * 70)
    print(f"Target Subnet:       {NETWORK_SUBNET}.0/24")
    print(f"Hosts Scanned:       {PROPAGATION_ATTEMPTS}")
    print(f"Targets Found:       {len(targets)}")
    print(f"Exploits Sent:       {exploits}")
    print(f"Payloads Delivered:  {payloads}")
    print(f"Lateral Moves:       {lateral}")
    print(f"Replications:        {replication}")
    print(f"Total Duration:      {total_time:.1f}s")
    print(f"Activity Rate:       {(exploits + payloads + lateral + replication) / total_time:.1f} actions/s")

    print("\n" + "=" * 70)
    print("EXPECTED IDS/IPS DETECTION")
    print("=" * 70)
    print("✓ Rule-Based Detection:")
    print("  - Category: WORMS / MASS_SCANNING")
    print("  - Severity: CRITICAL")
    print("  - Patterns:")
    print("    • Rapid network scanning")
    print("    • Multiple exploit attempts")
    print("    • Mass payload delivery")
    print("    • Lateral movement")
    print("    • Self-replication behavior")
    print("")
    print("✓ ML Detection:")
    print("  - Extremely high scan rate")
    print("  - Concurrent connections")
    print("  - Exponential propagation pattern")
    print("  - Worm-like behavior signature")
    print("")
    print("✓ Behavioral Analysis:")
    print("  - Network-wide scanning")
    print("  - Automated exploitation")
    print("  - Rapid spreading pattern")
    print("=" * 70)

    print("\nCheck the IDS/IPS 'Network Monitor' tab for detection alerts!")
    print("Expected alert: '🚨 CRITICAL: Worm propagation detected'\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

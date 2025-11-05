#!/usr/bin/env python3
"""
Attack Simulation Framework for IDS/IPS Testing

⚠️  AUTHORIZED USE ONLY ⚠️
This tool is designed ONLY for testing your own IDS/IPS systems on networks
you own or have explicit written permission to test.

Unauthorized network scanning, port scanning, or attack simulation against
systems you do not own is illegal and unethical.

USE CASES:
✓ Testing your own IDS/IPS detection capabilities
✓ Security research in controlled lab environments
✓ Educational demonstrations with proper authorization
✓ Penetration testing with signed agreements

Purpose: Generate controlled attack patterns to validate ML-based intrusion
detection and ensure the system correctly identifies threats.
"""

import socket
import struct
import time
import random
import threading
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import ipaddress


class AttackSimulator(ABC):
    """Base class for all attack simulations"""

    def __init__(self, target_ip: str, target_port: int = 80):
        self.target_ip = target_ip
        self.target_port = target_port
        self.results = []
        self.is_running = False

    @abstractmethod
    def simulate(self) -> Dict:
        """Simulate the attack and return results"""
        pass

    def log_event(self, event_type: str, details: str):
        """Log simulation event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'target': f"{self.target_ip}:{self.target_port}",
            'details': details
        }
        self.results.append(event)
        print(f"[{event['timestamp']}] {event_type}: {details}")

    def validate_target(self) -> bool:
        """Validate target is accessible and authorized"""
        try:
            # Check if target is localhost or private network
            ip = ipaddress.ip_address(self.target_ip)
            if ip.is_loopback or ip.is_private:
                return True
            else:
                print(f"⚠️  WARNING: Target {self.target_ip} is not a private/local address!")
                print("   Ensure you have authorization before proceeding.")
                response = input("   Do you have written authorization to test this target? (yes/no): ")
                return response.lower() == 'yes'
        except:
            return False


class PortScanSimulator(AttackSimulator):
    """Simulates port scanning reconnaissance"""

    def __init__(self, target_ip: str, port_range: Tuple[int, int] = (1, 1024)):
        super().__init__(target_ip)
        self.port_range = port_range

    def simulate(self) -> Dict:
        """Simulate port scanning attack"""
        self.log_event("PORT_SCAN", f"Starting port scan: ports {self.port_range[0]}-{self.port_range[1]}")

        open_ports = []
        scan_start = time.time()

        for port in range(self.port_range[0], min(self.port_range[1] + 1, 65536)):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                result = sock.connect_ex((self.target_ip, port))

                if result == 0:
                    open_ports.append(port)
                    self.log_event("PORT_OPEN", f"Port {port} is open")

                sock.close()
                time.sleep(0.01)  # Slight delay to avoid overwhelming

            except Exception as e:
                self.log_event("PORT_ERROR", f"Error scanning port {port}: {e}")

        scan_duration = time.time() - scan_start

        return {
            'attack_type': 'Reconnaissance',
            'sub_type': 'Port Scan',
            'duration': scan_duration,
            'ports_scanned': self.port_range[1] - self.port_range[0] + 1,
            'open_ports': open_ports,
            'packets_sent': self.port_range[1] - self.port_range[0] + 1
        }


class SynFloodSimulator(AttackSimulator):
    """Simulates SYN flood DoS attack"""

    def __init__(self, target_ip: str, target_port: int = 80, duration: int = 5):
        super().__init__(target_ip, target_port)
        self.duration = duration

    def simulate(self) -> Dict:
        """Simulate SYN flood attack"""
        self.log_event("DOS_ATTACK", f"Starting SYN flood for {self.duration} seconds")

        packets_sent = 0
        start_time = time.time()

        while time.time() - start_time < self.duration:
            try:
                # Create raw socket (requires admin/root)
                # For testing without raw sockets, we'll use connection attempts
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)

                # Attempt connection (simulates SYN packet)
                try:
                    sock.connect((self.target_ip, self.target_port))
                except:
                    pass  # Connection failure is expected

                sock.close()
                packets_sent += 1

                # Small delay to control rate
                time.sleep(0.001)

            except Exception as e:
                self.log_event("DOS_ERROR", f"Error: {e}")
                break

        duration = time.time() - start_time

        return {
            'attack_type': 'DoS',
            'sub_type': 'SYN Flood',
            'duration': duration,
            'packets_sent': packets_sent,
            'rate': packets_sent / duration if duration > 0 else 0
        }


class ServiceFuzzingSimulator(AttackSimulator):
    """Simulates fuzzing attacks on services"""

    def __init__(self, target_ip: str, target_port: int = 80):
        super().__init__(target_ip, target_port)

    def generate_fuzz_payload(self) -> bytes:
        """Generate random malformed data"""
        patterns = [
            b'A' * random.randint(1000, 5000),  # Buffer overflow
            b'\x00' * random.randint(100, 500),  # Null bytes
            b'\xff\xfe' * random.randint(50, 200),  # Invalid UTF-16
            b'%s%s%s%s%s%s%s%s',  # Format string
            b'../../../etc/passwd',  # Path traversal
            b'<script>alert(1)</script>',  # XSS
            b"' OR '1'='1",  # SQL injection
        ]
        return random.choice(patterns)

    def simulate(self) -> Dict:
        """Simulate fuzzing attack"""
        self.log_event("FUZZING", f"Starting fuzzing attack")

        requests_sent = 0
        anomalies_detected = 0
        start_time = time.time()

        for i in range(50):  # Send 50 fuzzed requests
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((self.target_ip, self.target_port))

                # Send fuzzed payload
                payload = self.generate_fuzz_payload()
                sock.send(payload)

                # Try to receive response
                try:
                    response = sock.recv(1024)
                    if len(response) == 0 or b'error' in response.lower():
                        anomalies_detected += 1
                except:
                    anomalies_detected += 1

                sock.close()
                requests_sent += 1
                time.sleep(0.1)

            except Exception as e:
                self.log_event("FUZZ_ERROR", f"Error: {e}")

        duration = time.time() - start_time

        return {
            'attack_type': 'Fuzzers',
            'sub_type': 'Service Fuzzing',
            'duration': duration,
            'requests_sent': requests_sent,
            'anomalies_detected': anomalies_detected
        }


class ExploitSimulator(AttackSimulator):
    """Simulates exploitation attempts"""

    def __init__(self, target_ip: str, target_port: int = 80):
        super().__init__(target_ip, target_port)

    def simulate(self) -> Dict:
        """Simulate exploitation attempts"""
        self.log_event("EXPLOIT", "Starting exploitation simulation")

        exploit_attempts = [
            b'GET /../../../etc/passwd HTTP/1.1\r\n\r\n',
            b'POST / HTTP/1.1\r\nContent-Length: -1\r\n\r\n',
            b'GET / HTTP/1.1\r\nHost: ' + b'A' * 10000 + b'\r\n\r\n',
            b'\x90' * 100 + b'\x31\xc0\x50\x68\x2f\x2f\x73\x68',  # NOP sled + shellcode
        ]

        attempts = 0

        for payload in exploit_attempts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((self.target_ip, self.target_port))
                sock.send(payload)

                try:
                    response = sock.recv(1024)
                    self.log_event("EXPLOIT_ATTEMPT", f"Sent exploit payload, got {len(response)} bytes response")
                except:
                    self.log_event("EXPLOIT_ATTEMPT", "Sent exploit payload, no response")

                sock.close()
                attempts += 1
                time.sleep(0.5)

            except Exception as e:
                self.log_event("EXPLOIT_ERROR", f"Error: {e}")

        return {
            'attack_type': 'Exploits',
            'sub_type': 'Remote Exploitation',
            'attempts': attempts,
            'payloads_sent': len(exploit_attempts)
        }


class BackdoorSimulator(AttackSimulator):
    """Simulates backdoor communication patterns"""

    def __init__(self, target_ip: str, target_port: int = 4444):
        super().__init__(target_ip, target_port)

    def simulate(self) -> Dict:
        """Simulate backdoor communication"""
        self.log_event("BACKDOOR", "Starting backdoor communication simulation")

        # Simulate periodic beacons (typical of backdoors)
        beacons_sent = 0

        for i in range(10):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)

                # Attempt connection to unusual port (backdoor behavior)
                try:
                    sock.connect((self.target_ip, self.target_port))
                    # Send beacon
                    beacon = b'BEACON_' + str(i).encode()
                    sock.send(beacon)
                    beacons_sent += 1
                    self.log_event("BACKDOOR_BEACON", f"Sent beacon {i}")
                except:
                    self.log_event("BACKDOOR_BEACON", f"Beacon {i} failed (expected if no backdoor)")

                sock.close()
                time.sleep(2)  # Periodic beacons every 2 seconds

            except Exception as e:
                self.log_event("BACKDOOR_ERROR", f"Error: {e}")

        return {
            'attack_type': 'Backdoor',
            'sub_type': 'Command & Control',
            'beacons_sent': beacons_sent,
            'beacon_interval': 2
        }


class ReconnaissanceSimulator(AttackSimulator):
    """Simulates network reconnaissance"""

    def __init__(self, target_network: str):
        super().__init__(target_network)
        self.target_network = target_network

    def simulate(self) -> Dict:
        """Simulate network reconnaissance"""
        self.log_event("RECON", f"Starting reconnaissance of {self.target_network}")

        # Parse network CIDR
        try:
            network = ipaddress.ip_network(self.target_network, strict=False)
        except:
            return {'error': 'Invalid network address'}

        hosts_discovered = []

        # Scan up to 10 hosts to avoid overwhelming
        count = 0
        for ip in network.hosts():
            if count >= 10:
                break

            try:
                # ICMP ping simulation (using TCP as substitute)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((str(ip), 80))

                if result == 0:
                    hosts_discovered.append(str(ip))
                    self.log_event("HOST_DISCOVERED", f"Host alive: {ip}")

                sock.close()
                count += 1
                time.sleep(0.1)

            except Exception as e:
                pass

        return {
            'attack_type': 'Reconnaissance',
            'sub_type': 'Network Scanning',
            'hosts_scanned': count,
            'hosts_discovered': len(hosts_discovered),
            'discovered_ips': hosts_discovered
        }


def print_banner():
    """Print warning banner"""
    print("\n" + "=" * 70)
    print("  ⚠️  ATTACK SIMULATION FRAMEWORK - AUTHORIZED USE ONLY  ⚠️")
    print("=" * 70)
    print("\nThis tool generates network traffic that mimics real attacks.")
    print("Use ONLY on systems you own or have written permission to test.")
    print("\nSupported simulations:")
    print("  • Port Scanning (Reconnaissance)")
    print("  • SYN Flood (DoS)")
    print("  • Service Fuzzing (Fuzzers)")
    print("  • Exploitation Attempts (Exploits)")
    print("  • Backdoor Communication (Backdoor)")
    print("  • Network Reconnaissance (Reconnaissance)")
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    print_banner()

    print("Example usage:")
    print("  from attack_simulator import PortScanSimulator")
    print("  sim = PortScanSimulator('127.0.0.1', (20, 100))")
    print("  results = sim.simulate()")
    print("\nSee test_ids_ips.py for complete testing suite")

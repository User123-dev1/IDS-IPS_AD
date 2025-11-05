#!/usr/bin/env python3
"""
IDS/IPS Attack Detection Test Suite

Runs comprehensive attack simulations to validate that the ML-based IDS/IPS
correctly identifies various threat categories.

⚠️  AUTHORIZED USE ONLY ⚠️
Run only on your own systems or with written authorization.
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from attack_simulator import (
    PortScanSimulator,
    SynFloodSimulator,
    ServiceFuzzingSimulator,
    ExploitSimulator,
    BackdoorSimulator,
    ReconnaissanceSimulator,
    print_banner
)


class IDSIPSTestSuite:
    """Comprehensive test suite for IDS/IPS validation"""

    def __init__(self, target_ip: str = '127.0.0.1'):
        self.target_ip = target_ip
        self.test_results = []

    def run_all_tests(self) -> Dict:
        """Run all attack simulations"""
        print("\n" + "=" * 70)
        print("  IDS/IPS DETECTION TEST SUITE")
        print("=" * 70)
        print(f"\nTarget: {self.target_ip}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "=" * 70 + "\n")

        tests = [
            ("Port Scan Attack", self.test_port_scanning),
            ("DoS Attack (SYN Flood)", self.test_dos_attack),
            ("Fuzzing Attack", self.test_fuzzing),
            ("Exploitation Attempts", self.test_exploits),
            ("Backdoor Communication", self.test_backdoor),
            ("Network Reconnaissance", self.test_reconnaissance),
        ]

        for test_name, test_func in tests:
            print(f"\n{'=' * 70}")
            print(f"  TEST: {test_name}")
            print(f"{'=' * 70}\n")

            try:
                result = test_func()
                result['test_name'] = test_name
                result['status'] = 'completed'
                self.test_results.append(result)
                print(f"\n✓ {test_name} completed")
            except Exception as e:
                print(f"\n✗ {test_name} failed: {e}")
                self.test_results.append({
                    'test_name': test_name,
                    'status': 'failed',
                    'error': str(e)
                })

            time.sleep(2)  # Pause between tests

        self.print_summary()
        return {'tests': self.test_results}

    def test_port_scanning(self) -> Dict:
        """Test 1: Port Scanning Detection"""
        print("Simulating aggressive port scanning...")
        print("Expected: IDS should detect reconnaissance activity\n")

        sim = PortScanSimulator(self.target_ip, port_range=(20, 100))
        results = sim.simulate()

        print(f"\nResults:")
        print(f"  Ports scanned: {results['ports_scanned']}")
        print(f"  Open ports found: {len(results['open_ports'])}")
        print(f"  Duration: {results['duration']:.2f}s")

        return results

    def test_dos_attack(self) -> Dict:
        """Test 2: DoS Attack Detection"""
        print("Simulating SYN flood DoS attack...")
        print("Expected: IDS should detect abnormal connection rate\n")

        sim = SynFloodSimulator(self.target_ip, target_port=80, duration=5)
        results = sim.simulate()

        print(f"\nResults:")
        print(f"  Packets sent: {results['packets_sent']}")
        print(f"  Rate: {results['rate']:.1f} packets/sec")
        print(f"  Duration: {results['duration']:.2f}s")

        return results

    def test_fuzzing(self) -> Dict:
        """Test 3: Fuzzing Attack Detection"""
        print("Simulating service fuzzing with malformed data...")
        print("Expected: IDS should detect anomalous payloads\n")

        sim = ServiceFuzzingSimulator(self.target_ip, target_port=80)
        results = sim.simulate()

        print(f"\nResults:")
        print(f"  Fuzzed requests sent: {results['requests_sent']}")
        print(f"  Anomalies detected: {results['anomalies_detected']}")
        print(f"  Duration: {results['duration']:.2f}s")

        return results

    def test_exploits(self) -> Dict:
        """Test 4: Exploitation Attempt Detection"""
        print("Simulating exploitation attempts...")
        print("Expected: IDS should detect exploit signatures\n")

        sim = ExploitSimulator(self.target_ip, target_port=80)
        results = sim.simulate()

        print(f"\nResults:")
        print(f"  Exploit attempts: {results['attempts']}")
        print(f"  Payloads sent: {results['payloads_sent']}")

        return results

    def test_backdoor(self) -> Dict:
        """Test 5: Backdoor Communication Detection"""
        print("Simulating backdoor C&C traffic...")
        print("Expected: IDS should detect unusual port usage and beaconing\n")

        sim = BackdoorSimulator(self.target_ip, target_port=4444)
        results = sim.simulate()

        print(f"\nResults:")
        print(f"  Beacons sent: {results['beacons_sent']}")
        print(f"  Beacon interval: {results['beacon_interval']}s")

        return results

    def test_reconnaissance(self) -> Dict:
        """Test 6: Network Reconnaissance Detection"""
        print("Simulating network reconnaissance...")
        print("Expected: IDS should detect scanning activity\n")

        sim = ReconnaissanceSimulator(f"{self.target_ip}/29")
        results = sim.simulate()

        print(f"\nResults:")
        print(f"  Hosts scanned: {results.get('hosts_scanned', 0)}")
        print(f"  Hosts discovered: {results.get('hosts_discovered', 0)}")

        return results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("  TEST SUMMARY")
        print("=" * 70 + "\n")

        completed = sum(1 for t in self.test_results if t['status'] == 'completed')
        failed = sum(1 for t in self.test_results if t['status'] == 'failed')

        print(f"Total Tests: {len(self.test_results)}")
        print(f"Completed:   {completed}")
        print(f"Failed:      {failed}")

        print("\n" + "-" * 70)
        print("Attack Types Simulated:")
        print("-" * 70)

        for result in self.test_results:
            status_icon = "✓" if result['status'] == 'completed' else "✗"
            print(f"  {status_icon} {result['test_name']}")

        print("\n" + "=" * 70)
        print("  NEXT STEPS")
        print("=" * 70)
        print("\n1. Check IDS/IPS Dashboard:")
        print("   • Go to 'ML Detection' tab in main application")
        print("   • Review detected anomalies and alerts")
        print("   • Verify alerts match simulated attacks")
        print("\n2. Review Detection Logs:")
        print("   • Check if all 6 attack types were flagged")
        print("   • Validate attack categorization is correct")
        print("   • Review false positive/negative rates")
        print("\n3. Analyze ML Performance:")
        print("   • Go to 'ML Performance' tab")
        print("   • Check detection rates per attack category")
        print("   • Review confusion matrix for accuracy")
        print("\n4. Generate Security Report:")
        print("   • Use 'Export Results' to document findings")
        print("   • Compare against baseline behavior")
        print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point"""
    print_banner()

    # Warning and confirmation
    print("\n⚠️  WARNING: This will generate attack-like network traffic!")
    print("   Only run on systems you own or have authorization to test.\n")

    response = input("Do you have authorization to run these tests? (yes/no): ")

    if response.lower() != 'yes':
        print("\n❌ Tests cancelled. Obtain authorization before running.")
        return

    # Get target IP
    print("\nDefault target: 127.0.0.1 (localhost)")
    target = input("Enter target IP (press Enter for localhost): ").strip()

    if not target:
        target = '127.0.0.1'

    print(f"\nTarget: {target}")
    print("\nStarting test suite in 3 seconds...")
    time.sleep(3)

    # Run tests
    suite = IDSIPSTestSuite(target_ip=target)
    results = suite.run_all_tests()

    # Save results
    output_file = Path(__file__).parent / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(output_file, 'w') as f:
        f.write("IDS/IPS Test Results\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Target: {target}\n")
        f.write(f"Date: {datetime.now().isoformat()}\n\n")

        for result in results['tests']:
            f.write(f"\nTest: {result['test_name']}\n")
            f.write(f"Status: {result['status']}\n")
            if 'error' not in result:
                for key, value in result.items():
                    if key not in ['test_name', 'status']:
                        f.write(f"  {key}: {value}\n")

    print(f"\n📄 Results saved to: {output_file}")


if __name__ == "__main__":
    main()

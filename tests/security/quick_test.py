#!/usr/bin/env python3
"""
Quick IDS/IPS Test - Run a single attack simulation

Usage:
    python quick_test.py                    # Port scan on localhost
    python quick_test.py --attack dos       # DoS attack
    python quick_test.py --attack all       # All attacks
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from attack_simulator import (
    PortScanSimulator,
    SynFloodSimulator,
    ServiceFuzzingSimulator,
    ExploitSimulator,
    BackdoorSimulator,
    ReconnaissanceSimulator,
    print_banner
)


def run_single_attack(attack_type: str, target: str = '127.0.0.1'):
    """Run a single attack simulation"""

    print_banner()

    simulators = {
        'portscan': (PortScanSimulator, {'target_ip': target, 'port_range': (20, 100)}),
        'dos': (SynFloodSimulator, {'target_ip': target, 'target_port': 80, 'duration': 5}),
        'fuzzing': (ServiceFuzzingSimulator, {'target_ip': target, 'target_port': 80}),
        'exploit': (ExploitSimulator, {'target_ip': target, 'target_port': 80}),
        'backdoor': (BackdoorSimulator, {'target_ip': target, 'target_port': 4444}),
        'recon': (ReconnaissanceSimulator, {'target_network': f"{target}/29"}),
    }

    if attack_type not in simulators:
        print(f"❌ Unknown attack type: {attack_type}")
        print(f"Available: {', '.join(simulators.keys())}")
        return

    print(f"\n🎯 Target: {target}")
    print(f"🔥 Attack: {attack_type}")
    print("\nStarting in 2 seconds...\n")

    import time
    time.sleep(2)

    SimClass, kwargs = simulators[attack_type]
    sim = SimClass(**kwargs)
    results = sim.simulate()

    print("\n" + "=" * 70)
    print("  RESULTS")
    print("=" * 70 + "\n")

    for key, value in results.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("\n✓ Test complete! Check your IDS/IPS dashboard for alerts.")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Quick IDS/IPS attack simulation test'
    )

    parser.add_argument(
        '--attack',
        default='portscan',
        choices=['portscan', 'dos', 'fuzzing', 'exploit', 'backdoor', 'recon', 'all'],
        help='Type of attack to simulate (default: portscan)'
    )

    parser.add_argument(
        '--target',
        default='127.0.0.1',
        help='Target IP address (default: 127.0.0.1)'
    )

    args = parser.parse_args()

    if args.attack == 'all':
        print("\n⚠️  Running ALL attacks against", args.target)
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return

        attacks = ['portscan', 'dos', 'fuzzing', 'exploit', 'backdoor', 'recon']
        for attack in attacks:
            run_single_attack(attack, args.target)
            print("\n" + "-" * 70 + "\n")
            import time
            time.sleep(3)
    else:
        run_single_attack(args.attack, args.target)


if __name__ == "__main__":
    main()

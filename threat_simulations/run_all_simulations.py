#!/usr/bin/env python3
"""
Comprehensive Threat Simulation Test Runner

This script runs all attack simulations to comprehensively test the IDS/IPS system.
Can run simulations individually or in sequence.

Attack Categories Covered:
1. Port Scan & Reconnaissance
2. Brute Force
3. DoS/DDoS (SYN Flood)
4. Analysis & Fingerprinting
5. Backdoor & C2
6. Exploits
7. Fuzzers
8. Shellcode
9. Worms
10. Generic Malicious Traffic

⚠️ WARNING: Runs multiple attack simulations - use in test environment only!
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Simulation scripts
SIMULATIONS = [
    {
        'id': 1,
        'name': 'Port Scan & Reconnaissance',
        'script': 'threat_simulation_1_port_scan.py',
        'category': 'RECONNAISSANCE',
        'description': 'Network scanning and service enumeration'
    },
    {
        'id': 2,
        'name': 'Brute Force Attack',
        'script': 'threat_simulation_2_brute_force.py',
        'category': 'BRUTE_FORCE',
        'description': 'Credential brute forcing on SSH/RDP/FTP'
    },
    {
        'id': 3,
        'name': 'SYN Flood DoS Attack',
        'script': 'threat_simulation_3_syn_flood.py',
        'category': 'DOS_ATTACK',
        'description': 'Network flooding and denial of service'
    },
    {
        'id': 4,
        'name': 'Analysis & Fingerprinting',
        'script': 'threat_simulation_4_analysis.py',
        'category': 'ANALYSIS',
        'description': 'Service fingerprinting and reconnaissance'
    },
    {
        'id': 5,
        'name': 'Backdoor & C2 Communication',
        'script': 'threat_simulation_5_backdoor.py',
        'category': 'BACKDOOR',
        'description': 'Command & Control and persistence'
    },
    {
        'id': 6,
        'name': 'Exploit Attempts',
        'script': 'threat_simulation_6_exploits.py',
        'category': 'EXPLOITS',
        'description': 'SQL injection, buffer overflows, RCE'
    },
    {
        'id': 7,
        'name': 'Fuzzing & Malformed Packets',
        'script': 'threat_simulation_7_fuzzers.py',
        'category': 'FUZZERS',
        'description': 'Malformed requests and crash attempts'
    },
    {
        'id': 8,
        'name': 'Shellcode & Payload Delivery',
        'script': 'threat_simulation_8_shellcode.py',
        'category': 'SHELLCODE',
        'description': 'Binary payloads and code injection'
    },
    {
        'id': 9,
        'name': 'Worm Propagation',
        'script': 'threat_simulation_9_worms.py',
        'category': 'WORMS',
        'description': 'Mass scanning and self-replication'
    },
    {
        'id': 10,
        'name': 'Generic Malicious Traffic',
        'script': 'threat_simulation_10_generic.py',
        'category': 'GENERIC',
        'description': 'Mixed suspicious activities'
    },
]


def print_main_menu():
    """Print main menu"""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE THREAT SIMULATION TEST SUITE")
    print("=" * 80)
    print("\nAvailable Simulations:\n")

    for sim in SIMULATIONS:
        print(f"  [{sim['id']}] {sim['name']}")
        print(f"      Category: {sim['category']}")
        print(f"      {sim['description']}")
        print()

    print("=" * 80)
    print("\nOptions:")
    print("  [1-10]  Run specific simulation")
    print("  [ALL]   Run all simulations in sequence")
    print("  [QUICK] Run quick test (Port Scan + Brute Force + DoS)")
    print("  [EXIT]  Exit")
    print("=" * 80)


def run_simulation(sim_index, auto_yes=False):
    """Run a specific simulation"""
    if sim_index < 0 or sim_index >= len(SIMULATIONS):
        print(f"❌ Invalid simulation index: {sim_index + 1}")
        return False

    sim = SIMULATIONS[sim_index]
    script_path = Path(__file__).parent / sim['script']

    if not script_path.exists():
        print(f"❌ Simulation script not found: {sim['script']}")
        return False

    print("\n" + "=" * 80)
    print(f"RUNNING SIMULATION {sim['id']}: {sim['name']}")
    print("=" * 80)
    print(f"Category:    {sim['category']}")
    print(f"Description: {sim['description']}")
    print(f"Script:      {sim['script']}")
    print("=" * 80 + "\n")

    if not auto_yes:
        response = input("Continue with this simulation? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Simulation skipped.")
            return False

    try:
        # Run the simulation
        start_time = time.time()

        if auto_yes:
            # Auto-answer "yes" to confirmation prompts
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            output, _ = process.communicate(input="yes\n", timeout=300)
            print(output)
            returncode = process.returncode
        else:
            # Interactive mode
            returncode = subprocess.call([sys.executable, str(script_path)])

        duration = time.time() - start_time

        if returncode == 0:
            print(f"\n✅ Simulation completed successfully in {duration:.1f}s")
            return True
        else:
            print(f"\n❌ Simulation failed with code {returncode}")
            return False

    except subprocess.TimeoutExpired:
        print("\n⏱️  Simulation timed out (>5 minutes)")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Error running simulation: {e}")
        return False


def run_all_simulations():
    """Run all simulations in sequence"""
    print("\n" + "=" * 80)
    print("RUNNING ALL SIMULATIONS")
    print("=" * 80)
    print(f"Total simulations: {len(SIMULATIONS)}")
    print("\n⚠️  WARNING: This will run all attack simulations sequentially.")
    print("    This will generate significant network traffic.")
    print("    Ensure you have permission and this is a test environment!")
    print("=" * 80)

    response = input("\nContinue with ALL simulations? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cancelled.")
        return

    start_time = time.time()
    results = []

    for i, sim in enumerate(SIMULATIONS, 1):
        print(f"\n\n{'#' * 80}")
        print(f"# SIMULATION {i}/{len(SIMULATIONS)}")
        print(f"{'#' * 80}\n")

        success = run_simulation(i - 1, auto_yes=True)
        results.append({'simulation': sim['name'], 'success': success})

        if i < len(SIMULATIONS):
            print(f"\n⏸️  Waiting 5 seconds before next simulation...")
            time.sleep(5)

    total_duration = time.time() - start_time

    # Print summary
    print("\n\n" + "=" * 80)
    print("SIMULATION SUMMARY")
    print("=" * 80)

    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful

    print(f"\nTotal Simulations:  {len(results)}")
    print(f"Successful:         {successful} ✅")
    print(f"Failed:             {failed} ❌")
    print(f"Total Duration:     {total_duration / 60:.1f} minutes\n")

    print("Detailed Results:")
    print("-" * 80)
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"  [{i:2d}] {result['simulation']:40s} {status}")

    print("=" * 80)
    print("\n📊 Check the IDS/IPS Network Monitor for all detections!")
    print("    Expected: Multiple critical alerts across all categories\n")


def run_quick_test():
    """Run quick test suite (3 most common attacks)"""
    print("\n" + "=" * 80)
    print("RUNNING QUICK TEST SUITE")
    print("=" * 80)
    print("\nQuick test includes:")
    print("  1. Port Scan & Reconnaissance")
    print("  2. Brute Force Attack")
    print("  3. SYN Flood DoS Attack")
    print("\nThis provides basic IDS/IPS functionality verification.")
    print("=" * 80)

    response = input("\nContinue with quick test? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cancelled.")
        return

    quick_tests = [0, 1, 2]  # Indices for port scan, brute force, DoS

    for i, test_idx in enumerate(quick_tests, 1):
        print(f"\n\n{'#' * 80}")
        print(f"# QUICK TEST {i}/3")
        print(f"{'#' * 80}\n")

        run_simulation(test_idx, auto_yes=True)

        if i < len(quick_tests):
            print(f"\n⏸️  Waiting 3 seconds...")
            time.sleep(3)

    print("\n✅ Quick test complete!")
    print("📊 Check IDS/IPS for detections of Port Scan, Brute Force, and DoS\n")


def main():
    """Main menu loop"""
    while True:
        try:
            print_main_menu()
            choice = input("\nEnter your choice: ").strip().upper()

            if choice == 'EXIT' or choice == 'Q':
                print("\n👋 Exiting. Stay secure!\n")
                sys.exit(0)

            elif choice == 'ALL':
                run_all_simulations()
                input("\nPress Enter to return to menu...")

            elif choice == 'QUICK':
                run_quick_test()
                input("\nPress Enter to return to menu...")

            elif choice.isdigit() and 1 <= int(choice) <= len(SIMULATIONS):
                sim_index = int(choice) - 1
                run_simulation(sim_index)
                input("\nPress Enter to return to menu...")

            else:
                print(f"\n❌ Invalid choice: {choice}")
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(2)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting. Stay secure!\n")
        sys.exit(0)

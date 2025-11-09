#!/usr/bin/env python3
"""
Threat Simulation 8: Shellcode & Payload Delivery

This script simulates shellcode and payload delivery patterns:
- NOP sleds
- Shellcode patterns
- Encoded payloads
- Metasploit-style payloads
- Return-oriented programming (ROP) patterns
- Polymorphic shellcode

Expected Detection: Shellcode, Payload Delivery
⚠️ WARNING: Only use in authorized test environments!
"""

import socket
import time
import sys
from datetime import datetime

# Configuration
TARGET_IP = "127.0.0.1"
TARGET_PORTS = [80, 4444, 8080, 443]
DELAY = 0.5


def print_header():
    """Print simulation header"""
    print("=" * 70)
    print("THREAT SIMULATION 8: Shellcode & Payload Delivery")
    print("=" * 70)
    print(f"\nTarget IP:         {TARGET_IP}")
    print(f"Target Ports:      {TARGET_PORTS}")
    print(f"Delay:             {DELAY}s")
    print(f"\n⚠️  WARNING: This simulates shellcode delivery!")
    print("    Mimics exploit payload delivery and code injection.")
    print("    Only run on test networks with permission!")
    print("=" * 70)


def nop_sled_simulation(ip, port=80):
    """Simulate NOP sled (common in buffer overflow exploits)"""
    print(f"\n🛷 NOP Sled Simulation")
    print("-" * 70)

    nop_patterns = [
        b'\x90' * 500,  # x86 NOP
        b'\x41' * 500,  # INC ECX (alternative NOP)
        b'\x90\x90\x90\x90' * 125,  # Repeated NOPs
        b'\x90' * 200 + b'\xcc' * 100,  # NOP + INT3 (debugger break)
    ]

    sent = 0
    for nop_sled in nop_patterns:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, port))

            # Send NOP sled as part of exploit
            payload = b'A' * 100 + nop_sled + b'SHELLCODE'
            sock.send(payload)
            sock.close()
            sent += 1

            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Sent {len(nop_sled)} byte NOP sled")
            time.sleep(DELAY)

        except:
            pass

    print(f"✓ NOP sled patterns sent: {sent}")
    return sent


def shellcode_pattern_simulation(ip, port=4444):
    """Simulate common shellcode patterns"""
    print(f"\n💀 Shellcode Pattern Simulation")
    print("-" * 70)

    # Simulated shellcode patterns (NOT real executable code)
    shellcode_patterns = [
        # Linux x86 reverse shell pattern
        b'\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x50',

        # Windows reverse shell pattern
        b'\xfc\xe8\x82\x00\x00\x00\x60\x89\xe5\x31\xc0\x64\x8b\x50\x30',

        # Bind shell pattern
        b'\x6a\x66\x58\x6a\x01\x5b\x31\xd2\x52\x53\x6a\x02\x89\xe1\xcd\x80',

        # Meterpreter-style pattern
        b'\xfc\x48\x83\xe4\xf0\xe8\xc0\x00\x00\x00\x41\x51\x41\x50\x52',
    ]

    sent = 0
    for shellcode in shellcode_patterns:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, port))

            # Send as part of exploit payload
            exploit = b'A' * 200 + b'\x90' * 100 + shellcode + b'PADDING'
            sock.send(exploit)
            sock.close()
            sent += 1

            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Sent {len(shellcode)} byte shellcode")
            time.sleep(DELAY)

        except:
            pass

    print(f"✓ Shellcode patterns sent: {sent}")
    return sent


def encoded_payload_simulation(ip, port=80):
    """Simulate encoded payloads (IDS evasion)"""
    print(f"\n🔐 Encoded Payload Simulation")
    print("-" * 70)

    # Simulated encoded payloads
    encoded_payloads = [
        # URL encoded
        b'%2e%2e%2f%2e%2e%2f%65%74%63%2f%70%61%73%73%77%64',

        # Base64 encoded (common in web shells)
        b'c3lzdGVtKCRfR0VUWydjbWQnXSk7',  # system($_GET['cmd']);

        # Hex encoded
        b'\\x31\\xc0\\x50\\x68\\x2f\\x2f\\x73\\x68',

        # Unicode encoded
        b'\\u0063\\u006d\\u0064\\u002e\\u0065\\u0078\\u0065',

        # Double encoding
        b'%252e%252e%252f%252e%252e%252f',
    ]

    sent = 0
    for payload in encoded_payloads:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, port))

            request = b"GET /?data=" + payload + b" HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n"
            sock.send(request)
            sock.close()
            sent += 1

            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Sent encoded payload ({len(payload)} bytes)")
            time.sleep(DELAY)

        except:
            pass

    print(f"✓ Encoded payloads sent: {sent}")
    return sent


def metasploit_style_payload(ip, port=4444):
    """Simulate Metasploit-style payload delivery"""
    print(f"\n🎯 Metasploit-Style Payload Simulation")
    print("-" * 70)

    # Simulated Metasploit stager patterns
    payloads = [
        # Windows reverse_tcp stager
        b'\xfc\xe8\x82\x00\x00\x00\x60\x89\xe5\x31\xc0\x64\x8b\x50\x30\x8b\x52\x0c\x8b\x52\x14',

        # Linux bind_tcp stager
        b'\x31\xdb\xf7\xe3\x53\x43\x53\x6a\x02\x89\xe1\xb0\x66\xcd\x80\x5b\x5e\x52\x68',

        # Meterpreter payload
        b'\xfc\x48\x83\xe4\xf0\xe8\xc0\x00\x00\x00\x41\x51\x41\x50\x52\x51\x56\x48\x31\xd2',
    ]

    sent = 0
    for payload in payloads:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, port))

            # Metasploit typically sends staged payload
            sock.send(payload)
            sock.close()
            sent += 1

            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Sent Metasploit-style payload ({len(payload)} bytes)")
            time.sleep(DELAY)

        except:
            pass

    print(f"✓ Metasploit-style payloads sent: {sent}")
    return sent


def rop_chain_simulation(ip, port=80):
    """Simulate Return-Oriented Programming (ROP) patterns"""
    print(f"\n🔗 ROP Chain Simulation")
    print("-" * 70)

    # Simulated ROP gadgets (addresses)
    rop_chains = [
        # x86 ROP chain
        b'\x41' * 100 + b'\x10\x20\x30\x40' + b'\x50\x60\x70\x80' + b'\x90\xa0\xb0\xc0',

        # x64 ROP chain
        b'\x42' * 200 + b'\x00\x00\x00\x00\x40\x10\x20\x30' * 5,

        # Stack pivot ROP
        b'\x90' * 50 + b'\xff\xff\xff\xff' + b'\xaa\xbb\xcc\xdd' * 10,
    ]

    sent = 0
    for rop_chain in rop_chains:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, port))

            sock.send(rop_chain)
            sock.close()
            sent += 1

            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Sent ROP chain ({len(rop_chain)} bytes)")
            time.sleep(DELAY)

        except:
            pass

    print(f"✓ ROP chains sent: {sent}")
    return sent


def polymorphic_shellcode_simulation(ip, port=4444):
    """Simulate polymorphic shellcode (self-modifying)"""
    print(f"\n🎭 Polymorphic Shellcode Simulation")
    print("-" * 70)

    # Simulated polymorphic patterns (decoder stub + encrypted payload)
    polymorphic_patterns = [
        # XOR decoder stub + encrypted payload
        b'\xeb\x0b\x5e\x31\xc9\xb1\x32\x80\x36\xaa\x46\xe2\xfa' + b'\xaa' * 50,

        # ADD decoder stub
        b'\xeb\x10\x5e\x31\xc9\xb1\x40\x80\x06\x55\x46\xe2\xfa' + b'\x55' * 64,

        # Complex polymorphic decoder
        b'\xd9\xee\xd9\x74\x24\xf4\x5b\x31\xc9\xb1\x33\x83\xeb\xfc\x31\x5b' + b'\xff' * 100,
    ]

    sent = 0
    for pattern in polymorphic_patterns:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, port))

            sock.send(pattern)
            sock.close()
            sent += 1

            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Sent polymorphic shellcode ({len(pattern)} bytes)")
            time.sleep(DELAY)

        except:
            pass

    print(f"✓ Polymorphic shellcode sent: {sent}")
    return sent


def main():
    """Main shellcode simulation"""
    print_header()

    response = input("\nContinue with shellcode simulation? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Simulation cancelled.")
        return

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting shellcode delivery simulation...")
    print("-" * 70)

    total_sent = 0

    # Run all shellcode simulations
    total_sent += nop_sled_simulation(TARGET_IP)
    total_sent += shellcode_pattern_simulation(TARGET_IP)
    total_sent += encoded_payload_simulation(TARGET_IP)
    total_sent += metasploit_style_payload(TARGET_IP)
    total_sent += rop_chain_simulation(TARGET_IP)
    total_sent += polymorphic_shellcode_simulation(TARGET_IP)

    # Summary
    print("\n" + "=" * 70)
    print("SHELLCODE SIMULATION RESULTS")
    print("=" * 70)
    print(f"Target:              {TARGET_IP}")
    print(f"Total Payloads:      {total_sent}")
    print(f"Payload Types:       6")
    print("  - NOP Sleds:       4 patterns")
    print("  - Shellcode:       4 patterns")
    print("  - Encoded:         5 patterns")
    print("  - Metasploit:      3 patterns")
    print("  - ROP Chains:      3 patterns")
    print("  - Polymorphic:     3 patterns")

    print("\n" + "=" * 70)
    print("EXPECTED IDS/IPS DETECTION")
    print("=" * 70)
    print("✓ Rule-Based Detection:")
    print("  - Category: SHELLCODE / PAYLOAD_DELIVERY")
    print("  - Severity: CRITICAL")
    print("  - Signatures:")
    print("    • NOP sleds (\\x90 patterns)")
    print("    • Shellcode opcodes (\\x31\\xc0, \\xfc\\xe8)")
    print("    • Metasploit signatures")
    print("    • ROP gadget patterns")
    print("    • Polymorphic decoders")
    print("")
    print("✓ ML Detection:")
    print("  - Binary payload patterns")
    print("  - Unusual byte sequences")
    print("  - Exploit delivery behavior")
    print("")
    print("✓ Behavioral Analysis:")
    print("  - Shellcode injection attempts")
    print("  - Payload staging patterns")
    print("  - Code execution attempts")
    print("=" * 70)

    print("\nCheck the IDS/IPS 'Network Monitor' tab for detection alerts!")
    print("Expected alert: '🚨 CRITICAL: Shellcode/Payload delivery detected'\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

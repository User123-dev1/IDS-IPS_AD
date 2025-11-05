"""
Live Packet Capture Test
Tests actual network packet capture functionality
"""
import sys
import os
import time
from datetime import datetime

# Add src directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from scanner.secure_packet_capture import SecurePacketCapture, SCAPY_AVAILABLE


def main():
    print("=" * 80)
    print("LIVE PACKET CAPTURE TEST")
    print("=" * 80)

    if not SCAPY_AVAILABLE:
        print("\n[ERROR] Scapy not installed!")
        print("Install with: pip install scapy")
        print("\nOn Windows, also install Npcap: https://npcap.com/#download")
        return

    print("\n[INFO] This test will:")
    print("   1. Capture live network packets for 15 seconds")
    print("   2. Display captured packets in real-time")
    print("   3. Show statistics about what was captured")
    print("   4. Focus on industrial protocol traffic (Modbus, DNP3, etc.)")

    print("\n[WARNING] Requirements:")
    print("   * Administrator/root privileges")
    print("   * Npcap installed (Windows)")
    print("   * Active network connection")

    # Check if we should continue
    print("\n" + "=" * 80)
    input("Press ENTER to start capture (or Ctrl+C to cancel)...")

    try:
        capture = SecurePacketCapture()

        # Track packets
        packets_displayed = [0]
        max_display = 50  # Display first 50 packets

        def packet_callback(packet):
            """Display captured packets in real-time"""
            packets_displayed[0] += 1

            if packets_displayed[0] <= max_display:
                # Use ASCII markers instead of emojis
                protocol_marker = {
                    'Modbus/TCP': '[MOD]',
                    'DNP3': '[DNP]',
                    'OPC UA': '[OPC]',
                    'TCP': '[TCP]',
                    'UDP': '[UDP]'
                }

                marker = protocol_marker.get(packet.protocol, '[???]')

                timestamp = packet.timestamp.strftime("%H:%M:%S.%f")[:-3]

                print(f"{marker} {timestamp} | "
                      f"{packet.src_ip:15s}:{packet.src_port:<5d} -> "
                      f"{packet.dst_ip:15s}:{packet.dst_port:<5d} | "
                      f"{packet.protocol:15s} | {packet.size:5d} bytes | "
                      f"{packet.flags:15s}")

                # Show payload preview for industrial protocols
                if packet.protocol in ['Modbus/TCP', 'DNP3', 'OPC UA', 'S7comm']:
                    if packet.payload_preview:
                        print(f"     +-- Payload: {packet.payload_preview[:80]}")

            elif packets_displayed[0] == max_display + 1:
                print(f"\n... (showing first {max_display} packets, capture continues) ...\n")

        print("\n" + "=" * 80)
        print("CAPTURING PACKETS (15 seconds)...")
        print("=" * 80)
        print(
            f"{'Type':<6} {'Time':^12} | {'Source IP':^15}:{'Port':<5} -> {'Dest IP':^15}:{'Port':<5} | {'Protocol':^15} | {'Size':^5} | {'Flags'}")
        print("-" * 80)

        # Start capture
        success = capture.start_capture(
            callback=packet_callback,
            timeout=15,
            filter_expr=None  # Capture all traffic matching industrial ports
        )

        if not success:
            print("\n[ERROR] Failed to start capture!")
            print("\n[INFO] Common issues:")
            print("   * Not running as Administrator")
            print("   * Npcap not installed")
            print("   * No network interfaces available")
            return

        # Wait for capture to complete
        start_time = time.time()
        try:
            while capture.is_capturing and (time.time() - start_time) < 16:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\n[WARNING] Capture interrupted by user")

        # Stop capture
        capture.stop_capture()

        # Display results
        print("\n" + "=" * 80)
        print("CAPTURE RESULTS")
        print("=" * 80)

        stats = capture.get_statistics()

        print(f"\n[STATS] Overall Statistics:")
        print(f"   Total Packets Captured: {stats['packets_captured']}")
        print(f"   Packets Dropped:        {stats['packets_dropped']}")
        print(f"   Capture Duration:       15 seconds")
        if stats['packets_captured'] > 0:
            print(f"   Average Rate:           {stats['packets_captured'] / 15:.1f} packets/sec")

        if stats['protocols']:
            print(f"\n[PROTOCOLS] Detected:")
            print(f"   {'Protocol':<20} | {'Count':>10} | {'Percentage':>10}")
            print(f"   {'-' * 20}-+-{'-' * 10}-+-{'-' * 10}")

            total = sum(stats['protocols'].values())
            for proto, count in sorted(stats['protocols'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total * 100) if total > 0 else 0

                # Highlight industrial protocols
                if proto in ['Modbus/TCP', 'DNP3', 'OPC UA', 'S7comm', 'EtherNet/IP']:
                    proto_display = f"*** {proto}"
                else:
                    proto_display = f"    {proto}"

                print(f"   {proto_display:<20} | {count:>10} | {percentage:>9.1f}%")
        else:
            print(f"\n[WARNING] No packets captured matching industrial protocol ports")
            print(f"\n   Possible reasons:")
            print(f"   * No industrial devices on this network")
            print(f"   * Devices not actively communicating")
            print(f"   * Capture filter too restrictive")

        # Check for industrial protocols
        industrial_found = any(proto in stats['protocols']
                               for proto in ['Modbus/TCP', 'DNP3', 'OPC UA', 'S7comm', 'EtherNet/IP'])

        if industrial_found:
            print(f"\n[SUCCESS] Industrial Protocol Traffic Detected!")
            print(f"   Your network has active OT/ICS devices communicating")
        else:
            print(f"\n[INFO] No Industrial Protocol Traffic Detected")
            print(f"   This is normal for IT networks without OT/ICS devices")

        print("\n" + "=" * 80)
        print("CAPTURE TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        # Additional info
        print(f"\n[NOTES]")
        print(f"   * Capture filtered for common industrial protocol ports")
        print(f"   * All packet data was sanitized and validated")
        print(f"   * Security limits were enforced during capture")
        print(f"   * No raw packet data stored in memory")

    except PermissionError as e:
        print(f"\n[ERROR] Permission Denied!")
        print(f"\n[SOLUTION]")
        print(f"   1. Close this PowerShell window")
        print(f"   2. Right-click PowerShell -> 'Run as Administrator'")
        print(f"   3. Navigate to: cd C:\\Users\\otlaptop\\PycharmProjects\\OT_Asset_Manager")
        print(f"   4. Activate venv: .venv\\Scripts\\Activate.ps1")
        print(f"   5. Run again: python src/scanner/test_live_capture.py")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

        print(f"\n[TROUBLESHOOTING]")
        print(f"   * Ensure Npcap is installed: https://npcap.com/#download")
        print(f"   * Check network adapter is enabled")
        print(f"   * Try running as Administrator")


if __name__ == "__main__":
    main()

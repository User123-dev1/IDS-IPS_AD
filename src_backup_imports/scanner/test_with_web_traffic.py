"""
Test packet capture with web traffic
Generates HTTP/HTTPS traffic for testing
"""
import sys
import os
import time
import threading
from datetime import datetime

# Add src directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from scapy.all import sniff, IP, TCP, UDP, Raw
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

def generate_traffic():
    """Generate web traffic for testing"""
    import urllib.request

    print("\n[TRAFFIC GENERATOR] Starting...")
    time.sleep(2)  # Wait for capture to start

    sites = [
        'http://example.com',
        'http://www.google.com',
        'http://www.github.com'
    ]

    for i, site in enumerate(sites):
        try:
            print(f"[TRAFFIC] Request {i+1}/3: {site}")
            urllib.request.urlopen(site, timeout=5)
            time.sleep(1)
        except Exception as e:
            print(f"[TRAFFIC] {e}")

def main():
    print("=" * 80)
    print("PACKET CAPTURE TEST - Web Traffic")
    print("=" * 80)

    if not SCAPY_AVAILABLE:
        print("\n[ERROR] Scapy not installed!")
        return

    print("\n[INFO] This test will:")
    print("   1. Start packet capture")
    print("   2. Generate web traffic (HTTP requests)")
    print("   3. Display captured packets")
    print("   4. Show statistics")

    print("\n" + "=" * 80)
    input("Press ENTER to start...")

    packets_captured = [0]
    protocols = {}

    def packet_handler(packet):
        packets_captured[0] += 1

        try:
            if packet.haslayer(IP):
                ip = packet[IP]
                protocol = "IP"
                src_port = dst_port = 0

                if packet.haslayer(TCP):
                    tcp = packet[TCP]
                    protocol = f"TCP:{tcp.dport}"
                    src_port = tcp.sport
                    dst_port = tcp.dport

                    # Check for HTTP
                    if dst_port == 80 or src_port == 80:
                        protocol = "HTTP"
                    elif dst_port == 443 or src_port == 443:
                        protocol = "HTTPS"

                elif packet.haslayer(UDP):
                    udp = packet[UDP]
                    protocol = f"UDP:{udp.dport}"
                    src_port = udp.sport
                    dst_port = udp.dport

                # Count protocols
                protocols[protocol] = protocols.get(protocol, 0) + 1

                # Display first 20 packets
                if packets_captured[0] <= 20:
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(f"[{protocol:12s}] {timestamp} | "
                          f"{ip.src:15s}:{src_port:<5d} -> "
                          f"{ip.dst:15s}:{dst_port:<5d} | "
                          f"{len(packet):5d} bytes")

                elif packets_captured[0] == 21:
                    print("\n... (capture continues) ...\n")

        except Exception as e:
            pass

    print("\n" + "=" * 80)
    print("STARTING CAPTURE (10 seconds)...")
    print("=" * 80)
    print(f"{'Protocol':<14} {'Time':^12} | {'Source IP':^15}:{'Port':<5} -> {'Dest IP':^15}:{'Port':<5} | {'Size'}")
    print("-" * 80)

    # Start traffic generator in background
    traffic_thread = threading.Thread(target=generate_traffic, daemon=True)
    traffic_thread.start()

    try:
        # Capture all TCP/UDP traffic
        sniff(
            filter="tcp or udp",
            prn=packet_handler,
            store=False,
            timeout=10
        )

        print("\n" + "=" * 80)
        print("CAPTURE COMPLETE")
        print("=" * 80)

        print(f"\n[STATS] Overall Statistics:")
        print(f"   Total Packets: {packets_captured[0]}")
        print(f"   Capture Rate:  {packets_captured[0] / 10:.1f} packets/sec")

        if protocols:
            print(f"\n[PROTOCOLS] Detected:")
            print(f"   {'Protocol':<20} | {'Count':>10} | {'%':>8}")
            print(f"   {'-'*20}-+-{'-'*10}-+-{'-'*8}")

            total = sum(protocols.values())
            for proto, count in sorted(protocols.items(), key=lambda x: x[1], reverse=True):
                pct = (count / total * 100) if total > 0 else 0
                print(f"   {proto:<20} | {count:>10} | {pct:>7.1f}%")

        if packets_captured[0] > 0:
            print("\n[SUCCESS] Packet capture is WORKING!")
            print("[INFO] The module will detect industrial protocols when OT devices are present")
        else:
            print("\n[WARNING] No packets captured")
            print("[INFO] Check you're running as Administrator")

    except PermissionError:
        print("\n[ERROR] Permission Denied - Run as Administrator!")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

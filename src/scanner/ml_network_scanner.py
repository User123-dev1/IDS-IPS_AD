"""
Enhanced Network Scanner with ML Anomaly Detection
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scapy.all import AsyncSniffer, IP, TCP, UDP
from datetime import datetime
import threading

from scanner.ml_integration import MLAnomalyDetector


class MLNetworkScanner:
    """Network scanner with integrated ML anomaly detection"""

    def __init__(self, interface=None, model_path="data/models/unsw_nb15_model"):
        self.interface = interface
        self.is_running = False
        self.sniffer = None

        print("Initializing ML detector...")
        self.ml_detector = MLAnomalyDetector(model_path)

        self.packet_count = 0
        self.anomaly_count = 0
        self.lock = threading.Lock()
        self.anomaly_callbacks = []
        
    def add_anomaly_callback(self, callback):
        """Add callback for anomaly detection"""
        self.anomaly_callbacks.append(callback)
    
    def _packet_callback(self, packet):
        """Process each captured packet"""
        try:
            if not packet.haslayer(IP):
                return
            
            packet_data = self._extract_packet_data(packet)
            ml_result = self.ml_detector.analyze_packet(packet_data)
            
            with self.lock:
                self.packet_count += 1
                if ml_result['is_anomaly']:
                    self.anomaly_count += 1
            
            if ml_result['is_anomaly']:
                for callback in self.anomaly_callbacks:
                    try:
                        callback(packet_data, ml_result)
                    except Exception as e:
                        print(f"Error in callback: {e}")
            
        except Exception as e:
            print(f"Error processing packet: {e}")
    
    def _extract_packet_data(self, packet):
        """Extract relevant data from Scapy packet"""
        data = {
            'timestamp': datetime.now(),
            'src_ip': packet[IP].src if packet.haslayer(IP) else 'unknown',
            'dst_ip': packet[IP].dst if packet.haslayer(IP) else 'unknown',
            'packet_size': len(packet),
            'payload_size': 0,
            'protocol': 'Unknown',
            'src_port': 0,
            'dst_port': 0,
            'tcp_flags': 0
        }
        
        if packet.haslayer(TCP):
            data['protocol'] = 'TCP'
            data['src_port'] = packet[TCP].sport
            data['dst_port'] = packet[TCP].dport
            data['tcp_flags'] = int(packet[TCP].flags)
            if hasattr(packet[TCP], 'payload'):
                data['payload_size'] = len(bytes(packet[TCP].payload))
        elif packet.haslayer(UDP):
            data['protocol'] = 'UDP'
            data['src_port'] = packet[UDP].sport
            data['dst_port'] = packet[UDP].dport
            if hasattr(packet[UDP], 'payload'):
                data['payload_size'] = len(bytes(packet[UDP].payload))
        
        return data
    
    def start(self, packet_count=0):
        """Start capturing packets"""
        if self.is_running:
            print("Scanner already running")
            return
        
        print("\n" + "="*70)
        print("  ML-Powered Network Scanner")
        print("="*70)
        print(f"\nInterface: {self.interface or 'default'}")
        print(f"ML Detector: {'✓ Loaded' if self.ml_detector.is_loaded else '✗ Not loaded'}")
        print(f"Capture limit: {packet_count if packet_count > 0 else 'infinite'}")
        print("\nStarting capture... (Press Ctrl+C to stop)\n")
        
        self.is_running = True
        
        try:
            self.sniffer = AsyncSniffer(
                iface=self.interface,
                prn=self._packet_callback,
                store=False,
                count=packet_count if packet_count > 0 else 0
            )
            self.sniffer.start()
            self.sniffer.join()
            
        except KeyboardInterrupt:
            print("\n\nStopping capture...")
        except Exception as e:
            print(f"\nError during capture: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop capturing"""
        if self.sniffer:
            self.sniffer.stop()
        self.is_running = False
        self._print_statistics()
    
    def _print_statistics(self):
        """Print capture statistics"""
        stats = self.ml_detector.get_statistics()
        
        print("\n" + "="*70)
        print("  Capture Statistics")
        print("="*70)
        print(f"\nPackets Analyzed: {stats['total_packets']}")
        print(f"Anomalies Detected: {stats['anomaly_count']}")
        print(f"Anomaly Rate: {stats['anomaly_rate']:.2f}%")
        
        recent = self.ml_detector.get_recent_anomalies(limit=5)
        if recent:
            print(f"\nRecent Anomalies:")
            for i, anom in enumerate(recent[-5:], 1):
                print(f"  {i}. {anom['src_ip']} → {anom['dst_ip']} (score: {anom['score']:.2f})")
        
        print("="*70 + "\n")


if __name__ == "__main__":
    scanner = MLNetworkScanner()
    
    def on_anomaly(packet_data, ml_result):
        print(f"\n⚠ ANOMALY: {packet_data['src_ip']} → {packet_data['dst_ip']}")
        print(f"   Score: {ml_result['anomaly_score']:.3f} | {ml_result['details']}")
    
    scanner.add_anomaly_callback(on_anomaly)
    
    try:
        scanner.start(packet_count=100)  # Capture 100 packets
    except KeyboardInterrupt:
        print("\nExiting...")

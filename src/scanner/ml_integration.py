"""ML-Powered Anomaly Detection Integration"""
import sys
from pathlib import Path
from datetime import datetime
import threading
from collections import deque

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from ml.models.hybrid_detector import HybridAnomalyDetector
from ml.utils.feature_extraction import NetworkFeatureExtractor


class MLAnomalyDetector:
    """ML-powered anomaly detector for network traffic"""

    def __init__(self, model_path="data/models/unsw_nb15_model"):
        self.model_path = model_path
        self.detector = None
        self.extractor = NetworkFeatureExtractor()
        self.is_loaded = False
        self.lock = threading.Lock()

        self.total_packets = 0
        self.anomaly_count = 0
        self.anomaly_history = deque(maxlen=1000)

        self._load_model()
    
    def _load_model(self):
        """Load trained ML model"""
        try:
            model_file = Path(self.model_path + "_meta.json")
            if not model_file.exists():
                print(f"[WARNING] ML model not found at {self.model_path}")
                print("  Run training first: python src/ml/quick_start.py")
                return False
            
            self.detector = HybridAnomalyDetector()
            self.detector.load(self.model_path)
            self.is_loaded = True
            print(f"[OK] ML detector loaded from {self.model_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load ML model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def analyze_packet(self, packet_data):
        """Analyze a single packet for anomalies"""
        if not self.is_loaded:
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 'none',
                'details': 'ML detector not loaded'
            }
        
        try:
            with self.lock:
                features = self.extractor.extract_features(packet_data)
                result = self.detector.predict([features])
                
                is_anomaly = bool(result['is_anomaly'][0])
                score = float(result['anomaly_score'][0])
                
                if score < 0.3:
                    confidence = 'low'
                elif score < 0.7:
                    confidence = 'medium'
                else:
                    confidence = 'high'
                
                details = self._generate_details(packet_data, score, is_anomaly)
                
                self.total_packets += 1
                if is_anomaly:
                    self.anomaly_count += 1
                
                self.anomaly_history.append({
                    'timestamp': packet_data.get('timestamp', datetime.now()),
                    'is_anomaly': is_anomaly,
                    'score': score,
                    'src_ip': packet_data.get('src_ip', 'unknown'),
                    'dst_ip': packet_data.get('dst_ip', 'unknown')
                })
                
                return {
                    'is_anomaly': is_anomaly,
                    'anomaly_score': score,
                    'confidence': confidence,
                    'details': details
                }
                
        except Exception as e:
            print(f"Error in ML analysis: {e}")
            import traceback
            traceback.print_exc()
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 'error',
                'details': f'Analysis error: {str(e)}'
            }
    
    def _generate_details(self, packet_data, score, is_anomaly):
        """Generate human-readable anomaly details"""
        if not is_anomaly:
            return "Normal traffic pattern"
        
        details_parts = []
        
        pkt_size = packet_data.get('packet_size', 0)
        if pkt_size < 100:
            details_parts.append("unusually small packet")
        elif pkt_size > 1400:
            details_parts.append("unusually large packet")
        
        dst_port = packet_data.get('dst_port', 0)
        ics_ports = [502, 20000, 102, 47808, 44818, 4840]
        if dst_port not in ics_ports and dst_port < 1024:
            details_parts.append("non-standard port")
        
        src_ip = packet_data.get('src_ip', '')
        if not src_ip.startswith('192.168.') and not src_ip.startswith('10.'):
            details_parts.append("external source IP")
        
        if details_parts:
            return f"Anomaly: {', '.join(details_parts)} (score: {score:.2f})"
        else:
            return f"Anomaly detected with score {score:.2f}"
    
    def get_statistics(self):
        """Get detection statistics"""
        if self.total_packets == 0:
            anomaly_rate = 0.0
        else:
            anomaly_rate = (self.anomaly_count / self.total_packets) * 100
        
        return {
            'total_packets': self.total_packets,
            'anomaly_count': self.anomaly_count,
            'anomaly_rate': anomaly_rate,
            'is_loaded': self.is_loaded,
            'model_path': self.model_path
        }
    
    def get_recent_anomalies(self, limit=10):
        """Get recent anomalies"""
        anomalies = [a for a in self.anomaly_history if a['is_anomaly']]
        return list(anomalies)[-limit:]
    
    def reset_statistics(self):
        """Reset statistics counters"""
        with self.lock:
            self.total_packets = 0
            self.anomaly_count = 0
            self.anomaly_history.clear()


_global_detector = None

def get_ml_detector(model_path="data/models/unsw_nb15_model"):
    """Get global ML detector instance"""
    global _global_detector
    if _global_detector is None:
        _global_detector = MLAnomalyDetector(model_path)
    return _global_detector


def quick_analyze(packet_data):
    """Quick analysis function"""
    detector = get_ml_detector()
    return detector.analyze_packet(packet_data)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  Testing ML Anomaly Detector")
    print("="*70)
    
    detector = MLAnomalyDetector()
    
    if detector.is_loaded:
        # Test 1: Normal packet
        print("\n[Test 1] Normal ICS Traffic:")
        normal_packet = {
            'src_ip': '192.168.1.10',
            'dst_ip': '192.168.1.50',
            'src_port': 50123,
            'dst_port': 502,
            'protocol': 'TCP',
            'packet_size': 200,
            'payload_size': 150,
            'timestamp': datetime.now(),
            'tcp_flags': 24
        }
        
        result = detector.analyze_packet(normal_packet)
        print(f"  Source: {normal_packet['src_ip']}:{normal_packet['src_port']}")
        print(f"  Dest:   {normal_packet['dst_ip']}:{normal_packet['dst_port']} (Modbus)")
        print(f"  Result: {'[ANOMALY]' if result['is_anomaly'] else '[NORMAL]'}")
        print(f"  Score:  {result['anomaly_score']:.3f}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Details: {result['details']}")
        
        # Test 2: Suspicious packet
        print("\n[Test 2] Suspicious External Traffic:")
        suspicious_packet = {
            'src_ip': '8.8.8.8',
            'dst_ip': '192.168.1.50',
            'src_port': 50123,
            'dst_port': 22,
            'protocol': 'TCP',
            'packet_size': 1500,
            'payload_size': 1450,
            'timestamp': datetime.now(),
            'tcp_flags': 2
        }
        
        result = detector.analyze_packet(suspicious_packet)
        print(f"  Source: {suspicious_packet['src_ip']}:{suspicious_packet['src_port']}")
        print(f"  Dest:   {suspicious_packet['dst_ip']}:{suspicious_packet['dst_port']} (SSH)")
        print(f"  Result: {'[ANOMALY]' if result['is_anomaly'] else '[NORMAL]'}")
        print(f"  Score:  {result['anomaly_score']:.3f}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Details: {result['details']}")
        
        # Test 3: Port scan
        print("\n[Test 3] Potential Port Scan:")
        portscan_packet = {
            'src_ip': '192.168.1.100',
            'dst_ip': '192.168.1.50',
            'src_port': 54321,
            'dst_port': 3389,
            'protocol': 'TCP',
            'packet_size': 60,
            'payload_size': 0,
            'timestamp': datetime.now(),
            'tcp_flags': 2
        }
        
        result = detector.analyze_packet(portscan_packet)
        print(f"  Source: {portscan_packet['src_ip']}:{portscan_packet['src_port']}")
        print(f"  Dest:   {portscan_packet['dst_ip']}:{portscan_packet['dst_port']} (RDP)")
        print(f"  Result: {'[ANOMALY]' if result['is_anomaly'] else '[NORMAL]'}")
        print(f"  Score:  {result['anomaly_score']:.3f}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Details: {result['details']}")
        
        # Statistics
        print("\n" + "="*70)
        print("  Detection Statistics")
        print("="*70)
        stats = detector.get_statistics()
        print(f"  Total Packets Analyzed: {stats['total_packets']}")
        print(f"  Anomalies Detected:     {stats['anomaly_count']}")
        print(f"  Anomaly Rate:           {stats['anomaly_rate']:.1f}%")
        
        print("\n" + "="*70)
        print("  [SUCCESS] Test Complete! ML Detector Working!")
        print("="*70 + "\n")
    else:
        print("\n" + "="*70)
        print("  [ERROR] ML Detector Not Loaded")
        print("="*70)
        print("\nPossible reasons:")
        print("  1. Model not trained yet")
        print("  2. Model files missing in data/models/")
        print("  3. TensorFlow/scikit-learn not installed")
        print("\nTo fix:")
        print("  python src/ml/quick_start.py")
        print("="*70 + "\n")

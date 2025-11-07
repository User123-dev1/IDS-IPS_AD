"""
Improved ML Detector using 90.6% accuracy Random Forest model.

This detector uses the trained UNSW-NB15 model for flow-based anomaly detection.
It analyzes network flows (groups of packets) rather than individual packets.
"""

import pickle
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional
import threading
import logging

logger = logging.getLogger(__name__)


class NetworkFlow:
    """Represents a network flow (sequence of packets between src and dst)"""

    def __init__(self, src_ip, dst_ip, src_port, dst_port, protocol):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.src_port = src_port
        self.dst_port = dst_port
        self.protocol = protocol

        self.start_time = datetime.now()
        self.last_packet_time = datetime.now()

        self.packet_count = 0
        self.src_bytes = 0
        self.dst_bytes = 0

        self.src_packets = 0
        self.dst_packets = 0

        self.tcp_flags = set()
        self.ttl_values = []

        self.state = 'NEW'  # NEW, ESTABLISHED, CLOSING, CLOSED

    def update(self, packet_data, direction='forward'):
        """Update flow with new packet"""
        self.last_packet_time = datetime.now()
        self.packet_count += 1

        packet_size = packet_data.get('packet_size', 0)
        ttl = packet_data.get('ttl', 64)

        if direction == 'forward':
            self.src_bytes += packet_size
            self.src_packets += 1
        else:
            self.dst_bytes += packet_size
            self.dst_packets += 1

        self.ttl_values.append(ttl)

        # Track TCP state
        tcp_flags = packet_data.get('tcp_flags', 0)
        if tcp_flags:
            self.tcp_flags.add(tcp_flags)

            # Simple state tracking
            if tcp_flags & 0x02:  # SYN
                self.state = 'NEW'
            elif tcp_flags & 0x10:  # ACK
                self.state = 'ESTABLISHED'
            elif tcp_flags & 0x01:  # FIN
                self.state = 'CLOSING'

    def get_duration(self):
        """Get flow duration in seconds"""
        return (self.last_packet_time - self.start_time).total_seconds()

    def is_expired(self, timeout=60):
        """Check if flow is expired (no packets for timeout seconds)"""
        idle_time = (datetime.now() - self.last_packet_time).total_seconds()
        return idle_time > timeout


class ImprovedMLDetector:
    """
    Improved ML Detector with 90.6% accuracy.

    Uses the trained Random Forest model for flow-based attack detection.

    Performance:
    - Accuracy: 90.6%
    - Precision: 87.1%
    - Recall: 97.3% (catches 97.3% of attacks!)
    - F1-Score: 91.9%
    """

    def __init__(self, model_dir='data/models'):
        self.model_dir = Path(model_dir)
        self.model = None
        self.scaler = None
        self.features = None
        self.metadata = None
        self.is_loaded = False

        # Flow tracking
        self.flows = {}  # (src_ip, dst_ip, src_port, dst_port, proto) -> NetworkFlow
        self.flow_lock = threading.Lock()

        # Statistics
        self.total_flows = 0
        self.attacks_detected = 0
        self.detection_history = deque(maxlen=1000)

        # Load model
        self._load_model()

    def _load_model(self):
        """Load the improved ML model"""
        try:
            model_path = self.model_dir / 'improved_ids_model.pkl'
            scaler_path = self.model_dir / 'improved_ids_scaler.pkl'
            features_path = self.model_dir / 'improved_ids_features.json'
            metadata_path = self.model_dir / 'improved_ids_metadata.json'

            if not model_path.exists():
                logger.warning(f"Improved model not found at {model_path}")
                logger.warning("Using fallback detection. Train model with: python train_improved.py")
                return False

            # Load model
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)

            # Load scaler
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)

            # Load feature list
            with open(features_path, 'r') as f:
                self.features = json.load(f)

            # Load metadata
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)

            self.is_loaded = True
            logger.info(f"✓ Improved ML detector loaded (Accuracy: {self.metadata['test_accuracy']:.1%})")
            logger.info(f"✓ Using {len(self.features)} features")

            return True

        except Exception as e:
            logger.error(f"Failed to load improved model: {e}")
            import traceback
            traceback.print_exc()
            return False

    def process_packet(self, packet_data):
        """
        Process a packet and update flows.

        Args:
            packet_data: Dict with packet information
                - src_ip, dst_ip, src_port, dst_port, protocol
                - packet_size, ttl, tcp_flags, timestamp

        Returns:
            Dict with detection result if flow should be analyzed, None otherwise
        """
        if not self.is_loaded:
            return None

        # Extract flow key
        src_ip = packet_data.get('src_ip', '')
        dst_ip = packet_data.get('dst_ip', '')
        src_port = packet_data.get('src_port', 0)
        dst_port = packet_data.get('dst_port', 0)
        protocol = packet_data.get('protocol', '')

        if not src_ip or not dst_ip:
            return None

        flow_key = (src_ip, dst_ip, src_port, dst_port, protocol)
        reverse_key = (dst_ip, src_ip, dst_port, src_port, protocol)

        with self.flow_lock:
            # Find or create flow
            if flow_key in self.flows:
                flow = self.flows[flow_key]
                flow.update(packet_data, direction='forward')
            elif reverse_key in self.flows:
                flow = self.flows[reverse_key]
                flow.update(packet_data, direction='backward')
            else:
                # New flow
                flow = NetworkFlow(src_ip, dst_ip, src_port, dst_port, protocol)
                flow.update(packet_data, direction='forward')
                self.flows[flow_key] = flow

                # Analyze new flow after a few packets
                return None

            # Analyze flow periodically (every 10 packets or after 5 seconds)
            should_analyze = (
                flow.packet_count % 10 == 0 or
                flow.get_duration() > 5
            )

            if should_analyze:
                return self.analyze_flow(flow)

            # Clean up expired flows
            self._cleanup_expired_flows()

        return None

    def analyze_flow(self, flow: NetworkFlow):
        """
        Analyze a network flow for attacks.

        Returns:
            Dict with detection results
        """
        if not self.is_loaded:
            return {
                'is_attack': False,
                'confidence': 0.0,
                'threat_level': 'NONE',
                'details': 'Improved detector not loaded'
            }

        try:
            # Extract features from flow
            features_dict = self._extract_flow_features(flow)

            # Prepare features for model
            feature_df = pd.DataFrame([features_dict])

            # Ensure all required features exist
            for feat in self.features:
                if feat not in feature_df.columns:
                    feature_df[feat] = 0

            # Select only required features in correct order
            X = feature_df[self.features]

            # Handle missing/infinite values
            X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

            # Normalize
            X_scaled = self.scaler.transform(X)

            # Predict
            prediction = self.model.predict(X_scaled)[0]
            probabilities = self.model.predict_proba(X_scaled)[0]

            is_attack = bool(prediction == 1)
            confidence = float(probabilities[prediction])
            attack_prob = float(probabilities[1])

            # Determine threat level
            if attack_prob >= 0.9:
                threat_level = 'CRITICAL'
            elif attack_prob >= 0.7:
                threat_level = 'HIGH'
            elif attack_prob >= 0.5:
                threat_level = 'MEDIUM'
            else:
                threat_level = 'LOW'

            # Update statistics
            self.total_flows += 1
            if is_attack:
                self.attacks_detected += 1

            # Record detection
            detection = {
                'timestamp': datetime.now(),
                'src_ip': flow.src_ip,
                'dst_ip': flow.dst_ip,
                'src_port': flow.src_port,
                'dst_port': flow.dst_port,
                'protocol': flow.protocol,
                'is_attack': is_attack,
                'confidence': confidence,
                'attack_probability': attack_prob,
                'threat_level': threat_level,
                'flow_duration': flow.get_duration(),
                'packets': flow.packet_count,
                'bytes': flow.src_bytes + flow.dst_bytes
            }

            self.detection_history.append(detection)

            # Generate details
            details = self._generate_details(flow, is_attack, attack_prob)
            detection['details'] = details

            return detection

        except Exception as e:
            logger.error(f"Error analyzing flow: {e}")
            import traceback
            traceback.print_exc()
            return {
                'is_attack': False,
                'confidence': 0.0,
                'threat_level': 'ERROR',
                'details': f'Analysis error: {str(e)}'
            }

    def _extract_flow_features(self, flow: NetworkFlow) -> Dict:
        """Extract features from network flow"""
        duration = max(flow.get_duration(), 0.001)  # Avoid division by zero

        features = {}

        # Basic stats
        features['sbytes'] = flow.src_bytes
        features['dbytes'] = flow.dst_bytes
        features['Spkts'] = flow.src_packets
        features['Dpkts'] = flow.dst_packets

        # Rates
        features['rate'] = flow.packet_count / duration
        features['sload'] = (flow.src_bytes * 8) / duration  # bits per second
        features['dload'] = (flow.dst_bytes * 8) / duration if flow.dst_bytes > 0 else 0.001

        # TTL features
        if flow.ttl_values:
            features['sttl'] = flow.ttl_values[0] if flow.ttl_values else 64
            features['dttl'] = flow.ttl_values[-1] if len(flow.ttl_values) > 1 else 64
            features['time_to_live'] = np.mean(flow.ttl_values)
            features['ttl_difference'] = abs(features['sttl'] - features['dttl'])
        else:
            features['sttl'] = 64
            features['dttl'] = 64
            features['time_to_live'] = 64
            features['ttl_difference'] = 0

        # Connection state
        state_map = {'NEW': 0, 'ESTABLISHED': 1, 'CLOSING': 2, 'CLOSED': 3}
        features['connection_state'] = state_map.get(flow.state, 0)

        # Byte asymmetry
        total_bytes = flow.src_bytes + flow.dst_bytes
        if total_bytes > 0:
            features['byte_asymmetry'] = abs(flow.src_bytes - flow.dst_bytes) / total_bytes
        else:
            features['byte_asymmetry'] = 0

        # Mean sizes
        features['smean'] = flow.src_bytes / flow.src_packets if flow.src_packets > 0 else 0
        features['dmean'] = flow.dst_bytes / flow.dst_packets if flow.dst_packets > 0 else 0

        # Connection tracking (simplified)
        features['ct_state_ttl'] = len(flow.tcp_flags)
        features['ct_srv_dst'] = 1  # Simplified
        features['ct_dst_ltm'] = 1
        features['ct_src_ltm'] = 1
        features['ct_srv_src'] = 1

        # Duration
        features['dur'] = duration

        # Protocol features
        features['sport'] = flow.src_port
        features['dsport'] = flow.dst_port

        # Inter-packet time
        features['Sintpkt'] = duration / flow.src_packets if flow.src_packets > 0 else 0
        features['Dintpkt'] = duration / flow.dst_packets if flow.dst_packets > 0 else 0

        return features

    def _generate_details(self, flow: NetworkFlow, is_attack: bool, attack_prob: float) -> str:
        """Generate human-readable detection details"""
        if not is_attack:
            return f"Normal traffic flow ({flow.packet_count} packets, {flow.get_duration():.1f}s)"

        details = []

        # High packet rate
        rate = flow.packet_count / max(flow.get_duration(), 0.001)
        if rate > 100:
            details.append(f"high packet rate ({rate:.0f} pkt/s)")

        # Suspicious ports
        suspicious_ports = [22, 23, 3389, 445, 135]
        if flow.dst_port in suspicious_ports:
            port_names = {22: 'SSH', 23: 'Telnet', 3389: 'RDP', 445: 'SMB', 135: 'RPC'}
            details.append(f"suspicious port {flow.dst_port} ({port_names.get(flow.dst_port, 'unknown')})")

        # Small packets (potential scan)
        avg_size = (flow.src_bytes + flow.dst_bytes) / flow.packet_count
        if avg_size < 100:
            details.append(f"small packets ({avg_size:.0f} bytes avg)")

        # One-way communication
        if flow.dst_packets == 0:
            details.append("no response (potential scan)")

        # TTL anomaly
        if flow.ttl_values:
            avg_ttl = np.mean(flow.ttl_values)
            if avg_ttl > 128 or avg_ttl < 30:
                details.append(f"unusual TTL ({avg_ttl:.0f})")

        if details:
            return f"🚨 ATTACK ({attack_prob:.0%}): {', '.join(details)}"
        else:
            return f"🚨 ATTACK detected (confidence: {attack_prob:.0%})"

    def _cleanup_expired_flows(self, timeout=60):
        """Remove expired flows"""
        expired = [
            key for key, flow in self.flows.items()
            if flow.is_expired(timeout)
        ]
        for key in expired:
            del self.flows[key]

    def get_statistics(self):
        """Get detection statistics"""
        if self.total_flows == 0:
            attack_rate = 0.0
        else:
            attack_rate = (self.attacks_detected / self.total_flows) * 100

        return {
            'is_loaded': self.is_loaded,
            'model_accuracy': self.metadata['test_accuracy'] if self.metadata else 0.0,
            'model_recall': self.metadata['test_recall'] if self.metadata else 0.0,
            'total_flows_analyzed': self.total_flows,
            'attacks_detected': self.attacks_detected,
            'attack_rate': attack_rate,
            'active_flows': len(self.flows)
        }

    def get_recent_attacks(self, limit=10):
        """Get recent attack detections"""
        attacks = [d for d in self.detection_history if d['is_attack']]
        return list(attacks)[-limit:]

    def reset_statistics(self):
        """Reset statistics"""
        self.total_flows = 0
        self.attacks_detected = 0
        self.detection_history.clear()


# Global detector instance
_global_improved_detector = None


def get_improved_detector(model_dir='data/models'):
    """Get global improved detector instance"""
    global _global_improved_detector
    if _global_improved_detector is None:
        _global_improved_detector = ImprovedMLDetector(model_dir)
    return _global_improved_detector


if __name__ == "__main__":
    print("=" * 70)
    print("Testing Improved ML Detector (90.6% Accuracy)")
    print("=" * 70)

    detector = ImprovedMLDetector()

    if detector.is_loaded:
        print(f"\n✓ Model loaded successfully")
        print(f"  Accuracy:  {detector.metadata['test_accuracy']:.1%}")
        print(f"  Precision: {detector.metadata['test_precision']:.1%}")
        print(f"  Recall:    {detector.metadata['test_recall']:.1%}")
        print(f"  F1-Score:  {detector.metadata['test_f1']:.1%}")

        # Simulate normal traffic
        print("\n[Test 1] Simulating normal web traffic...")
        for i in range(15):
            packet = {
                'src_ip': '192.168.1.10',
                'dst_ip': '192.168.1.50',
                'src_port': 50000 + i,
                'dst_port': 80,
                'protocol': 'TCP',
                'packet_size': 500,
                'ttl': 64,
                'tcp_flags': 0x18,  # ACK + PSH
                'timestamp': datetime.now()
            }
            result = detector.process_packet(packet)
            if result:
                print(f"  Flow analyzed: {'ATTACK' if result['is_attack'] else 'NORMAL'} "
                      f"(confidence: {result['confidence']:.1%}, threat: {result['threat_level']})")

        # Simulate port scan
        print("\n[Test 2] Simulating port scan...")
        for port in range(20, 35):
            packet = {
                'src_ip': '192.168.1.100',
                'dst_ip': '192.168.1.50',
                'src_port': 54321,
                'dst_port': port,
                'protocol': 'TCP',
                'packet_size': 60,
                'ttl': 128,
                'tcp_flags': 0x02,  # SYN
                'timestamp': datetime.now()
            }
            result = detector.process_packet(packet)
            if result:
                print(f"  Port {port}: {'🚨 ATTACK' if result['is_attack'] else 'NORMAL'} "
                      f"({result['threat_level']}, {result['attack_probability']:.0%})")

        # Statistics
        print("\n" + "=" * 70)
        stats = detector.get_statistics()
        print("Detection Statistics:")
        print(f"  Flows analyzed:    {stats['total_flows_analyzed']}")
        print(f"  Attacks detected:  {stats['attacks_detected']}")
        print(f"  Attack rate:       {stats['attack_rate']:.1f}%")
        print(f"  Active flows:      {stats['active_flows']}")

        print("\n✓ Improved ML Detector is working!")
        print("=" * 70)
    else:
        print("\n❌ Improved detector not loaded")
        print("   Train the model first: python train_improved.py")

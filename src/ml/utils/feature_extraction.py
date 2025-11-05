"""Feature Extraction for ICS Network Traffic"""
import numpy as np
from datetime import datetime
from collections import defaultdict

class NetworkFeatureExtractor:
    def __init__(self):
        self.packet_history = defaultdict(list)
        self.ics_ports = [502, 20000, 102, 47808, 44818, 4840]
        
    def extract_features(self, packet_data):
        """Extract 10 features from packet"""
        features = []
        
        # 1-2: Sizes (normalized)
        features.append(packet_data.get('packet_size', 0) / 1500.0)
        features.append(packet_data.get('payload_size', 0) / 1500.0)
        
        # 3: Port (normalized)
        dst_port = packet_data.get('dst_port', 0)
        features.append(dst_port / 65535.0)
        
        # 4: Is ICS protocol
        features.append(1.0 if dst_port in self.ics_ports else 0.0)
        
        # 5: Inter-arrival time
        src_ip = packet_data.get('src_ip', '')
        timestamp = packet_data.get('timestamp', datetime.now())
        if src_ip in self.packet_history and self.packet_history[src_ip]:
            inter_arrival = (timestamp - self.packet_history[src_ip][-1]).total_seconds()
            features.append(min(inter_arrival, 10.0) / 10.0)
        else:
            features.append(0.0)
        self.packet_history[src_ip].append(timestamp)
        if len(self.packet_history[src_ip]) > 100:
            self.packet_history[src_ip] = self.packet_history[src_ip][-100:]
        
        # 6: TCP flags
        features.append(packet_data.get('tcp_flags', 0) / 255.0)
        
        # 7-8: Time features
        hour = timestamp.hour if hasattr(timestamp, 'hour') else 0
        features.append(hour / 24.0)
        weekday = timestamp.weekday() if hasattr(timestamp, 'weekday') else 0
        features.append(weekday / 7.0)
        
        # 9: Packet rate
        recent = [t for t in self.packet_history[src_ip] if (timestamp - t).total_seconds() < 1.0]
        features.append(min(len(recent) / 100.0, 1.0))
        
        # 10: Is internal IP
        try:
            import ipaddress
            is_internal = ipaddress.ip_address(src_ip).is_private
        except:
            is_internal = False
        features.append(1.0 if is_internal else 0.0)
        
        return np.array(features, dtype=np.float32)
    
    def extract_batch(self, packet_list):
        return np.array([self.extract_features(p) for p in packet_list])
    
    def get_feature_names(self):
        return ['packet_size', 'payload_size', 'dst_port', 'is_ics', 
                'inter_arrival', 'tcp_flags', 'hour', 'weekday', 
                'packet_rate', 'is_internal']

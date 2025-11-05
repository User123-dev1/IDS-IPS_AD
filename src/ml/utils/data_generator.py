"""Sample Data Generator"""
import numpy as np
from datetime import datetime, timedelta
import random

class SampleDataGenerator:
    def __init__(self, seed=42):
        np.random.seed(seed)
        random.seed(seed)
        self.ics_ports = [502, 20000, 102, 47808, 44818, 4840]
        
    def generate_normal_traffic(self, n_samples=10000):
        packets = []
        base_time = datetime.now()
        for i in range(n_samples):
            packet = {
                'src_ip': f"192.168.1.{random.randint(1, 50)}",
                'dst_ip': f"192.168.1.{random.randint(51, 100)}",
                'src_port': random.randint(10000, 65535),
                'dst_port': random.choice(self.ics_ports),
                'protocol': 'TCP',
                'packet_size': int(np.random.normal(200, 50)),
                'payload_size': int(np.random.normal(150, 40)),
                'timestamp': base_time + timedelta(seconds=i*0.1 + np.random.uniform(0, 0.05)),
                'tcp_flags': random.choice([2, 16, 18, 24]),
            }
            packet['packet_size'] = max(packet['packet_size'], packet['payload_size'] + 40)
            packets.append(packet)
        return packets
    
    def generate_anomalous_traffic(self, n_samples=1000):
        packets = []
        base_time = datetime.now()
        for i in range(n_samples):
            anom_type = random.choice(['port_scan', 'ddos', 'unusual_size'])
            if anom_type == 'port_scan':
                packet = {
                    'src_ip': f"192.168.1.{random.randint(1, 254)}",
                    'dst_ip': "192.168.1.100",
                    'src_port': random.randint(30000, 60000),
                    'dst_port': random.randint(1, 65535),
                    'protocol': 'TCP',
                    'packet_size': 60,
                    'payload_size': 0,
                    'timestamp': base_time + timedelta(seconds=i*0.001),
                    'tcp_flags': 2,
                }
            elif anom_type == 'ddos':
                packet = {
                    'src_ip': f"10.0.0.{random.randint(1, 254)}",
                    'dst_ip': "192.168.1.50",
                    'src_port': random.randint(1024, 65535),
                    'dst_port': random.choice(self.ics_ports),
                    'protocol': 'TCP',
                    'packet_size': random.randint(500, 1500),
                    'payload_size': random.randint(400, 1400),
                    'timestamp': base_time + timedelta(seconds=i*0.001),
                    'tcp_flags': 2,
                }
            else:  # unusual_size
                packet = {
                    'src_ip': f"192.168.1.{random.randint(1, 50)}",
                    'dst_ip': f"192.168.1.{random.randint(51, 100)}",
                    'src_port': random.randint(10000, 65535),
                    'dst_port': random.choice(self.ics_ports),
                    'protocol': 'TCP',
                    'packet_size': random.choice([50, 1500, 9000]),
                    'payload_size': random.choice([10, 1450, 8950]),
                    'timestamp': base_time + timedelta(seconds=i*0.1),
                    'tcp_flags': 24,
                }
            packets.append(packet)
        return packets
    
    def generate_mixed_dataset(self, n_normal=10000, n_anomalous=500):
        normal = self.generate_normal_traffic(n_normal)
        anomalous = self.generate_anomalous_traffic(n_anomalous)
        all_packets = normal + anomalous
        labels = [0] * n_normal + [1] * n_anomalous
        combined = list(zip(all_packets, labels))
        random.shuffle(combined)
        packets, labels = zip(*combined)
        return list(packets), np.array(labels)

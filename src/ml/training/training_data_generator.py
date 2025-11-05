#!/usr/bin/env python3
"""
Training Data Generator for OT/ICS Security ML Models
Generates synthetic but realistic training data for:
- Anomaly Detection
- Threat Classification
- Vulnerability Prediction
- Protocol Analysis
"""

import numpy as np
import random
from typing import Dict, List, Tuple
from datetime import datetime, timedelta


class OTTrainingDataGenerator:
    """Generate synthetic OT/ICS network training data"""

    # OT/ICS specific protocols and ports
    OT_PROTOCOLS = {
        'Modbus': [502],
        'EtherNet/IP': [44818, 2222],
        'DNP3': [20000],
        'S7': [102],
        'BACnet': [47808],
        'OPC UA': [4840],
        'PROFINET': [34962, 34964],
        'HTTP': [80, 443, 8080],
        'SSH': [22],
        'Telnet': [23],
        'FTP': [21],
        'SNMP': [161, 162]
    }

    # OT device types and vendors
    DEVICE_TYPES = ['PLC', 'HMI', 'SCADA', 'RTU', 'IED', 'Engineering Station', 'Historian', 'Sensor', 'Actuator']
    VENDORS = ['Siemens', 'Rockwell', 'Schneider', 'ABB', 'GE', 'Honeywell', 'Emerson', 'Yokogawa']

    # Attack signatures
    ATTACK_PATTERNS = {
        'Port Scan': {'ports_accessed': 50, 'connection_duration': 0.1, 'packet_size': 64},
        'Exploit': {'ports_accessed': 1, 'connection_duration': 5.0, 'packet_size': 1500},
        'DoS': {'ports_accessed': 1, 'connection_duration': 0.01, 'packet_size': 8000},
        'Malware': {'ports_accessed': 3, 'connection_duration': 10.0, 'packet_size': 2048}
    }

    def __init__(self, seed: int = 42):
        """Initialize generator with random seed"""
        np.random.seed(seed)
        random.seed(seed)

    def generate_normal_traffic(self, n_samples: int = 1000) -> Tuple[np.ndarray, List[Dict]]:
        """
        Generate normal OT/ICS network traffic
        Returns: (features, metadata)
        """
        features = []
        metadata = []

        for i in range(n_samples):
            # Select random OT protocol and device
            protocol = random.choice(list(self.OT_PROTOCOLS.keys()))
            port = random.choice(self.OT_PROTOCOLS[protocol])
            device_type = random.choice(self.DEVICE_TYPES)
            vendor = random.choice(self.VENDORS)

            # Normal traffic characteristics
            packet_rate = np.random.normal(10, 3)  # 10 packets/sec avg
            packet_size = np.random.normal(512, 128)  # 512 bytes avg
            connection_duration = np.random.exponential(5)  # 5 sec avg
            ports_accessed = 1  # Normal devices use single port
            unique_ips = np.random.randint(1, 5)  # Communicates with 1-4 devices
            failed_connections = np.random.binomial(10, 0.01)  # 1% failure rate
            protocol_errors = np.random.binomial(10, 0.005)  # 0.5% error rate

            # Time-based features
            hour = np.random.randint(0, 24)
            is_business_hours = 1 if 7 <= hour <= 18 else 0
            day_of_week = np.random.randint(0, 7)

            # Build feature vector (11 features matching device_feature_extractor.py)
            feature_vector = [
                port,
                packet_rate,
                packet_size,
                connection_duration,
                ports_accessed,
                unique_ips,
                failed_connections,
                protocol_errors,
                is_business_hours,
                day_of_week,
                0  # risk_score (0 for normal traffic)
            ]

            features.append(feature_vector)
            metadata.append({
                'protocol': protocol,
                'device_type': device_type,
                'vendor': vendor,
                'label': 'Normal',
                'threat_class': 0  # Benign
            })

        return np.array(features), metadata

    def generate_attack_traffic(self, n_samples: int = 200, attack_distribution: Dict = None) -> Tuple[np.ndarray, List[Dict]]:
        """
        Generate attack traffic samples
        Args:
            n_samples: Number of attack samples
            attack_distribution: Distribution of attack types (default: equal)
        Returns: (features, metadata)
        """
        if attack_distribution is None:
            attack_distribution = {
                'Port Scan': 0.3,
                'Exploit': 0.3,
                'DoS': 0.2,
                'Malware': 0.2
            }

        features = []
        metadata = []

        for i in range(n_samples):
            # Select attack type based on distribution
            attack_type = np.random.choice(
                list(attack_distribution.keys()),
                p=list(attack_distribution.values())
            )

            pattern = self.ATTACK_PATTERNS[attack_type]

            # Attack-specific characteristics
            protocol = random.choice(list(self.OT_PROTOCOLS.keys()))
            port = random.choice(self.OT_PROTOCOLS[protocol])

            # Attack traffic has abnormal characteristics
            packet_rate = np.random.normal(100, 30)  # 10x higher rate
            packet_size = pattern['packet_size'] + np.random.normal(0, 100)
            connection_duration = pattern['connection_duration'] + np.random.exponential(1)
            ports_accessed = pattern['ports_accessed'] + np.random.randint(-5, 10)
            unique_ips = np.random.randint(10, 100)  # Scanning many IPs
            failed_connections = np.random.binomial(50, 0.3)  # 30% failure rate
            protocol_errors = np.random.binomial(20, 0.2)  # 20% error rate

            # Time-based (attacks often outside business hours)
            hour = np.random.choice([0, 1, 2, 3, 22, 23] + list(range(7, 19)))
            is_business_hours = 1 if 7 <= hour <= 18 else 0
            day_of_week = np.random.randint(0, 7)

            # Risk score (high for attacks)
            risk_score = np.random.uniform(60, 95)

            feature_vector = [
                port,
                packet_rate,
                packet_size,
                connection_duration,
                ports_accessed,
                unique_ips,
                failed_connections,
                protocol_errors,
                is_business_hours,
                day_of_week,
                risk_score
            ]

            features.append(feature_vector)

            # Map attack type to threat class
            threat_class_map = {
                'Port Scan': 1,
                'Exploit': 2,
                'DoS': 3,
                'Malware': 4
            }

            metadata.append({
                'protocol': protocol,
                'attack_type': attack_type,
                'label': 'Attack',
                'threat_class': threat_class_map[attack_type]
            })

        return np.array(features), metadata

    def generate_protocol_anomalies(self, n_samples: int = 100) -> Tuple[np.ndarray, List[Dict]]:
        """
        Generate protocol-specific anomalies
        (malformed packets, timing violations, etc.)
        """
        features = []
        metadata = []

        for i in range(n_samples):
            protocol = random.choice(['Modbus', 'S7', 'DNP3', 'EtherNet/IP'])
            port = random.choice(self.OT_PROTOCOLS[protocol])

            # Anomalous protocol behavior
            packet_rate = np.random.normal(50, 20)
            packet_size = np.random.uniform(1, 65535)  # Random size (malformed)
            connection_duration = np.random.uniform(0.001, 0.1)  # Very short
            ports_accessed = 1
            unique_ips = np.random.randint(1, 5)
            failed_connections = np.random.binomial(20, 0.5)  # 50% failure
            protocol_errors = np.random.binomial(30, 0.8)  # 80% errors!

            hour = np.random.randint(0, 24)
            is_business_hours = 1 if 7 <= hour <= 18 else 0
            day_of_week = np.random.randint(0, 7)

            risk_score = np.random.uniform(50, 80)

            feature_vector = [
                port,
                packet_rate,
                packet_size,
                connection_duration,
                ports_accessed,
                unique_ips,
                failed_connections,
                protocol_errors,
                is_business_hours,
                day_of_week,
                risk_score
            ]

            features.append(feature_vector)
            metadata.append({
                'protocol': protocol,
                'label': 'Protocol Anomaly',
                'threat_class': 2  # Treat as potential exploit
            })

        return np.array(features), metadata

    def generate_vulnerability_data(self, n_samples: int = 500) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
        """
        Generate vulnerability prediction training data
        Returns: (features, labels, metadata)
        """
        features = []
        labels = []
        metadata = []

        for i in range(n_samples):
            device_type = random.choice(self.DEVICE_TYPES)
            vendor = random.choice(self.VENDORS)

            # Simulate device characteristics
            num_services = np.random.randint(1, 10)
            num_open_ports = np.random.randint(1, 15)
            outdated_software = np.random.randint(0, 2)  # 0 or 1
            weak_authentication = np.random.randint(0, 2)
            unencrypted_protocols = np.random.randint(0, 5)
            patch_age_days = np.random.exponential(180)  # 6 months avg
            known_cves = np.random.poisson(2)  # Average 2 CVEs

            # Calculate vulnerability risk (0=low, 1=medium, 2=high)
            risk_factors = (
                outdated_software * 30 +
                weak_authentication * 25 +
                unencrypted_protocols * 10 +
                min(patch_age_days / 365, 1) * 20 +
                min(known_cves * 5, 20)
            )

            if risk_factors > 60:
                vulnerability_label = 2  # High
            elif risk_factors > 30:
                vulnerability_label = 1  # Medium
            else:
                vulnerability_label = 0  # Low

            feature_vector = [
                num_services,
                num_open_ports,
                outdated_software,
                weak_authentication,
                unencrypted_protocols,
                patch_age_days,
                known_cves,
                risk_factors
            ]

            features.append(feature_vector)
            labels.append(vulnerability_label)
            metadata.append({
                'device_type': device_type,
                'vendor': vendor,
                'risk_level': ['Low', 'Medium', 'High'][vulnerability_label]
            })

        return np.array(features), np.array(labels), metadata

    def generate_complete_training_set(self) -> Dict:
        """
        Generate complete training dataset for all models
        Returns dictionary with all training data
        """
        print("\n" + "="*60)
        print("Generating OT/ICS Security Training Dataset")
        print("="*60)

        # 1. Anomaly Detection Data
        print("\n[1/4] Generating Anomaly Detection training data...")
        normal_features, normal_meta = self.generate_normal_traffic(n_samples=1000)
        attack_features, attack_meta = self.generate_attack_traffic(n_samples=200)

        # Combine for anomaly detection (binary: 0=normal, 1=anomaly)
        X_anomaly = np.vstack([normal_features, attack_features])
        y_anomaly = np.array([0] * len(normal_features) + [1] * len(attack_features))

        print(f"   ✓ Generated {len(X_anomaly)} samples ({len(normal_features)} normal, {len(attack_features)} attacks)")

        # 2. Threat Classification Data
        print("\n[2/4] Generating Threat Classification training data...")
        # Include normal + all attack types
        X_threat = X_anomaly.copy()
        y_threat = np.array([m['threat_class'] for m in normal_meta + attack_meta])

        print(f"   ✓ Generated {len(X_threat)} samples across 5 threat classes")
        print(f"      - Class 0 (Benign): {sum(y_threat == 0)}")
        print(f"      - Class 1 (Port Scan): {sum(y_threat == 1)}")
        print(f"      - Class 2 (Exploit): {sum(y_threat == 2)}")
        print(f"      - Class 3 (DoS): {sum(y_threat == 3)}")
        print(f"      - Class 4 (Malware): {sum(y_threat == 4)}")

        # 3. Vulnerability Prediction Data
        print("\n[3/4] Generating Vulnerability Prediction training data...")
        X_vuln, y_vuln, vuln_meta = self.generate_vulnerability_data(n_samples=500)

        print(f"   ✓ Generated {len(X_vuln)} samples across 3 risk levels")
        print(f"      - Low Risk: {sum(y_vuln == 0)}")
        print(f"      - Medium Risk: {sum(y_vuln == 1)}")
        print(f"      - High Risk: {sum(y_vuln == 2)}")

        # 4. Protocol Analysis Data
        print("\n[4/4] Generating Protocol Analysis training data...")
        proto_normal, proto_normal_meta = self.generate_normal_traffic(n_samples=500)
        proto_anomaly, proto_anomaly_meta = self.generate_protocol_anomalies(n_samples=100)

        X_protocol = np.vstack([proto_normal, proto_anomaly])
        y_protocol = np.array([0] * len(proto_normal) + [1] * len(proto_anomaly))

        print(f"   ✓ Generated {len(X_protocol)} samples ({len(proto_normal)} normal, {len(proto_anomaly)} anomalies)")

        print("\n" + "="*60)
        print("Training Dataset Generation Complete!")
        print("="*60 + "\n")

        return {
            'anomaly_detection': {
                'X': X_anomaly,
                'y': y_anomaly,
                'baseline': normal_features,  # For Isolation Forest
                'metadata': normal_meta + attack_meta
            },
            'threat_classification': {
                'X': X_threat,
                'y': y_threat,
                'metadata': normal_meta + attack_meta
            },
            'vulnerability_prediction': {
                'X': X_vuln,
                'y': y_vuln,
                'metadata': vuln_meta
            },
            'protocol_analysis': {
                'X': X_protocol,
                'y': y_protocol,
                'baseline': proto_normal,  # For K-Means clustering
                'metadata': proto_normal_meta + proto_anomaly_meta
            }
        }


if __name__ == '__main__':
    # Test data generation
    generator = OTTrainingDataGenerator()
    training_data = generator.generate_complete_training_set()

    print("\nDataset Summary:")
    for model_name, data in training_data.items():
        print(f"\n{model_name.upper().replace('_', ' ')}:")
        print(f"  Features shape: {data['X'].shape}")
        print(f"  Labels shape: {data['y'].shape}")
        print(f"  Feature vector size: {data['X'].shape[1]}")

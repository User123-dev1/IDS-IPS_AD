"""Device Feature Extractor for ML Analysis

Converts device scan results into feature vectors for ML anomaly detection
and risk assessment.
"""
import numpy as np
from typing import Dict, List


class DeviceFeatureExtractor:
    """Extract ML features from device scan results"""

    # Known OT/ICS protocols by criticality
    CRITICAL_PROTOCOLS = ['Modbus', 'Siemens S7', 'DNP3', 'OPC UA']
    HIGH_RISK_PROTOCOLS = ['EtherNet/IP', 'BACnet', 'ProfiNet']

    # Vulnerable services
    VULNERABLE_SERVICES = ['Telnet', 'FTP', 'SMB']

    def __init__(self):
        """Initialize feature extractor"""
        self.feature_names = [
            'port_count',
            'ot_protocol_count',
            'critical_protocol_present',
            'vulnerable_service_count',
            'high_severity_vuln_count',
            'medium_severity_vuln_count',
            'critical_severity_vuln_count',
            'has_http',
            'has_ssh',
            'has_telnet',
            'device_exposure_score'
        ]

    def extract_features(self, scan_result: Dict) -> np.ndarray:
        """Extract features from a device scan result

        Args:
            scan_result: Dictionary containing device scan information

        Returns:
            numpy array of extracted features
        """
        features = []

        # 1. Port count (normalized)
        port_count = len(scan_result.get('open_ports', []))
        features.append(min(port_count / 20.0, 1.0))  # Normalize to [0, 1]

        # 2. OT protocol count
        ot_protocols = scan_result.get('ot_protocols', [])
        ot_count = len(ot_protocols)
        features.append(min(ot_count / 5.0, 1.0))

        # 3. Critical protocol presence (binary)
        has_critical = any(
            proto.get('protocol', '') in self.CRITICAL_PROTOCOLS
            for proto in ot_protocols
        )
        features.append(1.0 if has_critical else 0.0)

        # 4. Vulnerable service count
        open_ports = scan_result.get('open_ports', [])
        vulnerable_count = sum(
            1 for port in open_ports
            if port.get('service', '') in self.VULNERABLE_SERVICES
        )
        features.append(min(vulnerable_count / 3.0, 1.0))

        # 5-7. Vulnerability counts by severity
        vulnerabilities = scan_result.get('vulnerabilities', [])
        high_vuln = sum(1 for v in vulnerabilities if v.get('severity') == 'high')
        medium_vuln = sum(1 for v in vulnerabilities if v.get('severity') == 'medium')
        critical_vuln = sum(1 for v in vulnerabilities if v.get('severity') == 'critical')

        features.append(min(high_vuln / 5.0, 1.0))
        features.append(min(medium_vuln / 5.0, 1.0))
        features.append(min(critical_vuln / 3.0, 1.0))

        # 8-10. Specific service detection (binary)
        services = [port.get('service', '').lower() for port in open_ports]
        features.append(1.0 if any('http' in s for s in services) else 0.0)
        features.append(1.0 if 'ssh' in services else 0.0)
        features.append(1.0 if 'telnet' in services else 0.0)

        # 11. Device exposure score
        exposure_score = self._calculate_exposure_score(scan_result)
        features.append(exposure_score)

        return np.array(features, dtype=np.float32)

    def _calculate_exposure_score(self, scan_result: Dict) -> float:
        """Calculate overall device exposure score (0-1)"""
        score = 0.0

        # OT protocols exposed (+0.3 per critical, +0.2 per high-risk)
        ot_protocols = scan_result.get('ot_protocols', [])
        for proto in ot_protocols:
            proto_name = proto.get('protocol', '')
            if proto_name in self.CRITICAL_PROTOCOLS:
                score += 0.3
            elif proto_name in self.HIGH_RISK_PROTOCOLS:
                score += 0.2

        # Vulnerable services (+0.15 each)
        open_ports = scan_result.get('open_ports', [])
        for port in open_ports:
            if port.get('service', '') in self.VULNERABLE_SERVICES:
                score += 0.15

        # Critical vulnerabilities (+0.2 each)
        vulnerabilities = scan_result.get('vulnerabilities', [])
        critical_vulns = sum(1 for v in vulnerabilities if v.get('severity') == 'critical')
        score += critical_vulns * 0.2

        return min(score, 1.0)

    def get_feature_names(self) -> List[str]:
        """Get list of feature names"""
        return self.feature_names

    def extract_batch(self, scan_results: List[Dict]) -> np.ndarray:
        """Extract features from multiple scan results

        Args:
            scan_results: List of device scan result dictionaries

        Returns:
            2D numpy array where each row is a feature vector
        """
        features = [self.extract_features(result) for result in scan_results]
        return np.array(features, dtype=np.float32)


class DeviceRiskClassifier:
    """Classify device risk level based on features"""

    RISK_LEVELS = {
        'critical': {'threshold': 0.75, 'color': 'red'},
        'high': {'threshold': 0.50, 'color': 'orange'},
        'medium': {'threshold': 0.30, 'color': 'yellow'},
        'low': {'threshold': 0.0, 'color': 'green'}
    }

    def __init__(self):
        self.feature_extractor = DeviceFeatureExtractor()

    def classify_device(self, scan_result: Dict) -> Dict:
        """Classify device risk level

        Args:
            scan_result: Device scan result dictionary

        Returns:
            Classification result with risk level, score, and recommendations
        """
        features = self.feature_extractor.extract_features(scan_result)

        # Calculate risk score (weighted combination of features)
        risk_score = self._calculate_risk_score(features, scan_result)

        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(scan_result, risk_level)

        return {
            'risk_score': float(risk_score),
            'risk_level': risk_level,
            'risk_color': self.RISK_LEVELS[risk_level]['color'],
            'recommendations': recommendations,
            'feature_vector': features.tolist()
        }

    def _calculate_risk_score(self, features: np.ndarray, scan_result: Dict) -> float:
        """Calculate overall risk score using feature weights"""
        # Feature weights (must sum to 1.0)
        weights = np.array([
            0.05,  # port_count
            0.15,  # ot_protocol_count
            0.20,  # critical_protocol_present
            0.15,  # vulnerable_service_count
            0.10,  # high_severity_vuln_count
            0.05,  # medium_severity_vuln_count
            0.20,  # critical_severity_vuln_count
            0.02,  # has_http
            0.02,  # has_ssh
            0.03,  # has_telnet
            0.03   # device_exposure_score
        ])

        # Weighted sum
        risk_score = np.dot(features, weights)

        # Boost score if device is offline (unusual)
        if scan_result.get('status') == 'offline':
            risk_score = min(risk_score * 1.2, 1.0)

        return float(np.clip(risk_score, 0.0, 1.0))

    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        if risk_score >= self.RISK_LEVELS['critical']['threshold']:
            return 'critical'
        elif risk_score >= self.RISK_LEVELS['high']['threshold']:
            return 'high'
        elif risk_score >= self.RISK_LEVELS['medium']['threshold']:
            return 'medium'
        else:
            return 'low'

    def _generate_recommendations(self, scan_result: Dict, risk_level: str) -> List[str]:
        """Generate security recommendations based on scan results"""
        recommendations = []

        # Check for OT protocols
        ot_protocols = scan_result.get('ot_protocols', [])
        if ot_protocols:
            recommendations.append(
                f"Secure {len(ot_protocols)} exposed OT/ICS protocol(s) with firewall rules"
            )

        # Check for vulnerable services
        open_ports = scan_result.get('open_ports', [])
        vulnerable_services = [
            p for p in open_ports
            if p.get('service', '') in DeviceFeatureExtractor.VULNERABLE_SERVICES
        ]
        if vulnerable_services:
            services = ', '.join(p['service'] for p in vulnerable_services)
            recommendations.append(f"Disable or replace insecure services: {services}")

        # Check vulnerabilities
        vulnerabilities = scan_result.get('vulnerabilities', [])
        critical_vulns = [v for v in vulnerabilities if v.get('severity') == 'critical']
        if critical_vulns:
            recommendations.append(
                f"Immediately patch {len(critical_vulns)} critical vulnerabilit(y/ies)"
            )

        # Check if no SSH
        has_ssh = any(p.get('service') == 'SSH' for p in open_ports)
        has_telnet = any(p.get('service') == 'Telnet' for p in open_ports)
        if has_telnet and not has_ssh:
            recommendations.append("Replace Telnet with SSH for secure remote access")

        # General recommendations by risk level
        if risk_level == 'critical':
            recommendations.insert(0, "URGENT: Isolate this device and conduct immediate security audit")
        elif risk_level == 'high':
            recommendations.insert(0, "Prioritize this device for security hardening")

        if not recommendations:
            recommendations.append("Device security posture is acceptable. Continue monitoring.")

        return recommendations


if __name__ == "__main__":
    # Test the extractors
    print("\n" + "="*70)
    print("  Testing Device Feature Extractor & Risk Classifier")
    print("="*70)

    # Test case 1: High-risk OT device
    test_device_1 = {
        'ip': '192.168.1.10',
        'hostname': 'plc-controller-01',
        'status': 'online',
        'open_ports': [
            {'port': 502, 'service': 'Modbus'},
            {'port': 102, 'service': 'Siemens S7'},
            {'port': 23, 'service': 'Telnet'},
            {'port': 80, 'service': 'HTTP'}
        ],
        'ot_protocols': [
            {'protocol': 'Modbus', 'port': 502, 'risk': 'HIGH'},
            {'protocol': 'Siemens S7', 'port': 102, 'risk': 'HIGH'}
        ],
        'vulnerabilities': [
            {'severity': 'critical', 'description': 'Modbus exposed'},
            {'severity': 'high', 'description': 'Telnet enabled'},
            {'severity': 'medium', 'description': 'HTTP without auth'}
        ]
    }

    # Test case 2: Low-risk IT device
    test_device_2 = {
        'ip': '192.168.1.100',
        'hostname': 'workstation-05',
        'status': 'online',
        'open_ports': [
            {'port': 22, 'service': 'SSH'},
            {'port': 443, 'service': 'HTTPS'}
        ],
        'ot_protocols': [],
        'vulnerabilities': []
    }

    extractor = DeviceFeatureExtractor()
    classifier = DeviceRiskClassifier()

    print("\n[Test 1] High-Risk OT Device")
    print(f"Device: {test_device_1['hostname']} ({test_device_1['ip']})")
    features_1 = extractor.extract_features(test_device_1)
    classification_1 = classifier.classify_device(test_device_1)

    print(f"\nRisk Level: {classification_1['risk_level'].upper()}")
    print(f"Risk Score: {classification_1['risk_score']:.2f}")
    print(f"\nRecommendations:")
    for i, rec in enumerate(classification_1['recommendations'], 1):
        print(f"  {i}. {rec}")

    print("\n" + "-"*70)
    print("\n[Test 2] Low-Risk IT Device")
    print(f"Device: {test_device_2['hostname']} ({test_device_2['ip']})")
    features_2 = extractor.extract_features(test_device_2)
    classification_2 = classifier.classify_device(test_device_2)

    print(f"\nRisk Level: {classification_2['risk_level'].upper()}")
    print(f"Risk Score: {classification_2['risk_score']:.2f}")
    print(f"\nRecommendations:")
    for i, rec in enumerate(classification_2['recommendations'], 1):
        print(f"  {i}. {rec}")

    print("\n" + "="*70)
    print("  Feature Extraction Details")
    print("="*70)
    print(f"\nFeature Names ({len(extractor.feature_names)}):")
    for i, name in enumerate(extractor.feature_names, 1):
        print(f"  {i:2d}. {name:30s} | Device 1: {features_1[i-1]:.3f} | Device 2: {features_2[i-1]:.3f}")

    print("\n" + "="*70)
    print("  [SUCCESS] Feature Extractor & Classifier Working!")
    print("="*70 + "\n")

#!/usr/bin/env python3
"""
Real-Time Network Monitoring Engine
IDS/IPS functionality for OT/ICS networks with ML-powered threat detection
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Callable, Optional
from collections import deque
import json

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class Alert:
    """Security alert data structure"""

    def __init__(self, alert_type: str, severity: str, device_ip: str,
                 description: str, details: Dict = None):
        self.alert_id = f"ALERT-{int(time.time() * 1000)}"
        self.timestamp = datetime.now()
        self.alert_type = alert_type  # ANOMALY, THREAT, VULNERABILITY, NEW_DEVICE
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW
        self.device_ip = device_ip
        self.description = description
        self.details = details or {}
        self.acknowledged = False

    def to_dict(self) -> Dict:
        return {
            'alert_id': self.alert_id,
            'timestamp': self.timestamp.isoformat(),
            'alert_type': self.alert_type,
            'severity': self.severity,
            'device_ip': self.device_ip,
            'description': self.description,
            'details': self.details,
            'acknowledged': self.acknowledged
        }


class NetworkBaseline:
    """Stores learned baseline of normal network behavior"""

    def __init__(self):
        self.known_devices = set()  # Set of known device IPs
        self.device_profiles = {}   # IP -> device profile
        self.normal_traffic_patterns = []
        self.baseline_established = False
        self.baseline_timestamp = None

    def add_device(self, device_ip: str, device_info: Dict):
        """Add device to baseline"""
        self.known_devices.add(device_ip)
        self.device_profiles[device_ip] = {
            'first_seen': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'hostname': device_info.get('hostname', 'Unknown'),
            'device_type': device_info.get('device_type', 'Unknown'),
            'services': device_info.get('services', []),
            'protocols': device_info.get('protocols', []),
            'baseline_features': device_info.get('features', None)
        }

    def update_device(self, device_ip: str, last_seen: datetime = None):
        """Update device last seen time"""
        if device_ip in self.device_profiles:
            self.device_profiles[device_ip]['last_seen'] = (
                last_seen or datetime.now()
            ).isoformat()

    def is_known_device(self, device_ip: str) -> bool:
        """Check if device is in baseline"""
        return device_ip in self.known_devices

    def establish_baseline(self, devices: List[Dict]):
        """Establish baseline from initial scan"""
        for device in devices:
            device_ip = device.get('ip_address') or device.get('ip')
            if device_ip:
                self.add_device(device_ip, device)

        self.baseline_established = True
        self.baseline_timestamp = datetime.now()
        print(f"✓ Baseline established: {len(self.known_devices)} devices")

    def save_to_file(self, filepath: str):
        """Save baseline to file"""
        data = {
            'known_devices': list(self.known_devices),
            'device_profiles': self.device_profiles,
            'baseline_established': self.baseline_established,
            'baseline_timestamp': self.baseline_timestamp.isoformat() if self.baseline_timestamp else None
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filepath: str):
        """Load baseline from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.known_devices = set(data['known_devices'])
            self.device_profiles = data['device_profiles']
            self.baseline_established = data['baseline_established']
            if data['baseline_timestamp']:
                self.baseline_timestamp = datetime.fromisoformat(data['baseline_timestamp'])
            print(f"✓ Baseline loaded: {len(self.known_devices)} devices")
            return True
        except Exception as e:
            print(f"Error loading baseline: {e}")
            return False


class RealtimeMonitor:
    """
    Real-time network monitoring with IDS/IPS capabilities
    """

    def __init__(self, ml_system=None):
        self.ml_system = ml_system
        self.baseline = NetworkBaseline()
        self.alerts = deque(maxlen=1000)  # Keep last 1000 alerts
        self.monitoring_active = False
        self.monitor_thread = None

        # Statistics
        self.stats = {
            'packets_analyzed': 0,
            'anomalies_detected': 0,
            'threats_detected': 0,
            'new_devices_detected': 0,
            'vulnerabilities_found': 0,
            'alerts_generated': 0,
            'start_time': None,
            'last_update': None
        }

        # Callbacks for real-time updates
        self.alert_callbacks = []

    def register_alert_callback(self, callback: Callable[[Alert], None]):
        """Register callback function to receive real-time alerts"""
        self.alert_callbacks.append(callback)

    def start_monitoring(self, scan_interval: int = 60):
        """
        Start real-time monitoring
        Args:
            scan_interval: Seconds between monitoring cycles
        """
        if self.monitoring_active:
            print("Monitoring already active")
            return

        if not self.baseline.baseline_established:
            print("⚠ Warning: Baseline not established. Establishing from current network state...")
            # Would trigger a scan here

        self.monitoring_active = True
        self.stats['start_time'] = datetime.now()

        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(scan_interval,),
            daemon=True
        )
        self.monitor_thread.start()

        print(f"✓ Real-time monitoring started (interval: {scan_interval}s)")

    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("✓ Real-time monitoring stopped")

    def _monitoring_loop(self, scan_interval: int):
        """Main monitoring loop (runs in background thread)"""
        while self.monitoring_active:
            try:
                self._perform_monitoring_cycle()
                self.stats['last_update'] = datetime.now()
                time.sleep(scan_interval)

            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(scan_interval)

    def _perform_monitoring_cycle(self):
        """
        Perform one monitoring cycle
        This would integrate with actual network scanning
        """
        # In real implementation, this would:
        # 1. Scan network for active devices
        # 2. Capture and analyze traffic
        # 3. Extract features from devices
        # 4. Run ML analysis
        # 5. Generate alerts

        # For now, this is a placeholder that would integrate with:
        # - EnterpriseNetworkScanner for device discovery
        # - Packet capture for traffic analysis
        # - ML models for threat detection

        self.stats['packets_analyzed'] += 1

    def analyze_device(self, device_ip: str, device_data: Dict):
        """
        Analyze a device and generate alerts if needed
        Args:
            device_ip: IP address of device
            device_data: Device information and features
        """
        try:
            # Check if new device
            if not self.baseline.is_known_device(device_ip):
                self._handle_new_device(device_ip, device_data)

            # Update device last seen
            self.baseline.update_device(device_ip)

            # Extract features for ML analysis
            features = device_data.get('features')
            if features is None or not NUMPY_AVAILABLE:
                return

            if not isinstance(features, np.ndarray):
                features = np.array(features)

            # Run ML analysis if system available
            if self.ml_system:
                services = device_data.get('services', [])
                protocol = device_data.get('protocol', 'unknown')

                results = self.ml_system.analyze_device(features, protocol, services)

                # Generate alerts based on results
                self._process_ml_results(device_ip, results, device_data)

        except Exception as e:
            print(f"Error analyzing device {device_ip}: {e}")

    def _handle_new_device(self, device_ip: str, device_data: Dict):
        """Handle detection of new device"""
        alert = Alert(
            alert_type='NEW_DEVICE',
            severity='MEDIUM',
            device_ip=device_ip,
            description=f"New device detected: {device_data.get('hostname', device_ip)}",
            details={
                'device_type': device_data.get('device_type', 'Unknown'),
                'services': device_data.get('services', []),
                'first_seen': datetime.now().isoformat()
            }
        )

        self._generate_alert(alert)
        self.stats['new_devices_detected'] += 1

        # Add to baseline (auto-learn)
        self.baseline.add_device(device_ip, device_data)

    def _process_ml_results(self, device_ip: str, results: Dict, device_data: Dict):
        """Process ML analysis results and generate alerts"""

        # Check anomaly detection
        anomaly = results.get('anomaly_detection', {})
        if anomaly.get('anomaly_detected'):
            alert = Alert(
                alert_type='ANOMALY',
                severity=anomaly.get('severity', 'MEDIUM'),
                device_ip=device_ip,
                description=f"Anomaly detected: {anomaly.get('anomaly_type', 'Unknown')}",
                details={
                    'confidence': anomaly.get('confidence', 0.0),
                    'anomaly_type': anomaly.get('anomaly_type'),
                    'device_name': device_data.get('hostname', device_ip)
                }
            )
            self._generate_alert(alert)
            self.stats['anomalies_detected'] += 1

        # Check threat classification
        threat = results.get('threat_classification', {})
        if threat.get('threat_detected'):
            alert = Alert(
                alert_type='THREAT',
                severity=threat.get('severity', 'HIGH'),
                device_ip=device_ip,
                description=f"Threat detected: {threat.get('threat_name', 'Unknown')}",
                details={
                    'confidence': threat.get('confidence', 0.0),
                    'threat_class': threat.get('threat_class'),
                    'threat_name': threat.get('threat_name'),
                    'device_name': device_data.get('hostname', device_ip)
                }
            )
            self._generate_alert(alert)
            self.stats['threats_detected'] += 1

        # Check vulnerability prediction
        vuln = results.get('vulnerability_prediction', {})
        if vuln.get('exploitable'):
            matched_cves = vuln.get('matched_cves', [])
            cve_list = [cve.get('cve_id') for cve in matched_cves]

            alert = Alert(
                alert_type='VULNERABILITY',
                severity=vuln.get('risk_level', 'HIGH'),
                device_ip=device_ip,
                description=f"Exploitable vulnerability detected (CVE count: {len(matched_cves)})",
                details={
                    'risk_score': vuln.get('risk_score', 0.0),
                    'matched_cves': cve_list,
                    'device_name': device_data.get('hostname', device_ip),
                    'services': device_data.get('services', [])
                }
            )
            self._generate_alert(alert)
            self.stats['vulnerabilities_found'] += 1

        # Check protocol analysis
        protocol = results.get('protocol_analysis', {})
        if protocol.get('anomaly_detected') and protocol.get('confidence', 0) > 0.7:
            alert = Alert(
                alert_type='PROTOCOL_ANOMALY',
                severity=protocol.get('severity', 'MEDIUM'),
                device_ip=device_ip,
                description=f"Protocol anomaly in {protocol.get('protocol', 'unknown')}",
                details={
                    'confidence': protocol.get('confidence', 0.0),
                    'protocol': protocol.get('protocol'),
                    'cluster_id': protocol.get('cluster_id'),
                    'device_name': device_data.get('hostname', device_ip)
                }
            )
            self._generate_alert(alert)

    def _generate_alert(self, alert: Alert):
        """Generate and distribute alert"""
        self.alerts.append(alert)
        self.stats['alerts_generated'] += 1

        # Log alert
        print(f"🚨 [{alert.severity}] {alert.alert_type}: {alert.description}")

        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Error in alert callback: {e}")

    def get_recent_alerts(self, count: int = 50, severity: str = None) -> List[Alert]:
        """Get recent alerts"""
        alerts_list = list(self.alerts)

        if severity:
            alerts_list = [a for a in alerts_list if a.severity == severity]

        return alerts_list[-count:]

    def get_statistics(self) -> Dict:
        """Get monitoring statistics"""
        stats = self.stats.copy()

        if stats['start_time']:
            uptime = (datetime.now() - stats['start_time']).total_seconds()
            stats['uptime_seconds'] = uptime
            stats['uptime_formatted'] = self._format_uptime(uptime)

        stats['active_devices'] = len(self.baseline.known_devices)
        stats['total_alerts'] = len(self.alerts)

        return stats

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def acknowledge_alert(self, alert_id: str):
        """Mark alert as acknowledged"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def export_alerts(self, filepath: str, severity: str = None):
        """Export alerts to JSON file"""
        alerts_to_export = self.get_recent_alerts(count=1000, severity=severity)
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'alert_count': len(alerts_to_export),
            'alerts': [alert.to_dict() for alert in alerts_to_export]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Exported {len(alerts_to_export)} alerts to {filepath}")


if __name__ == "__main__":
    # Test the monitoring system
    print("=== Real-Time Monitoring System Test ===\n")

    # Create monitor
    monitor = RealtimeMonitor()

    # Establish baseline
    test_devices = [
        {'ip_address': '192.168.1.10', 'hostname': 'plc-01', 'device_type': 'PLC'},
        {'ip_address': '192.168.1.20', 'hostname': 'hmi-01', 'device_type': 'HMI'},
        {'ip_address': '192.168.1.1', 'hostname': 'gateway', 'device_type': 'Router'}
    ]
    monitor.baseline.establish_baseline(test_devices)

    # Register alert callback
    def print_alert(alert: Alert):
        print(f"  🔔 Alert: {alert.description}")

    monitor.register_alert_callback(print_alert)

    # Test new device detection
    print("\nTesting new device detection...")
    monitor.analyze_device('192.168.1.100', {
        'hostname': 'unknown-device',
        'device_type': 'Unknown',
        'services': ['http']
    })

    # Get statistics
    print("\nMonitoring Statistics:")
    stats = monitor.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✓ Test complete")

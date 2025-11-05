"""
Network Monitor Module
Passive monitoring of OT network traffic with anomaly detection
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .secure_packet_capture import SecurePacketCapture, PacketInfo
from .alert_rules_engine import AlertRulesEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DeviceProfile:
    """Profile of a discovered device"""
    ip_address: str
    mac_address: Optional[str] = None
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    protocols: set = field(default_factory=set)
    ports: set = field(default_factory=set)
    packet_count: int = 0
    byte_count: int = 0
    connections: set = field(default_factory=set)

    def update(self, packet: PacketInfo):
        """Update profile with new packet"""
        self.last_seen = datetime.now()
        self.packet_count += 1
        self.byte_count += packet.size
        self.protocols.add(packet.protocol)


@dataclass
class TrafficBaseline:
    """Baseline for normal traffic patterns"""
    avg_packets_per_minute: float = 0.0
    avg_bytes_per_minute: float = 0.0
    common_protocols: set = field(default_factory=set)
    common_ports: set = field(default_factory=set)
    typical_connections: set = field(default_factory=set)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class Anomaly:
    """Detected anomaly"""
    timestamp: datetime
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    category: str  # 'NEW_DEVICE', 'UNUSUAL_PROTOCOL', 'HIGH_TRAFFIC', etc.
    description: str
    source_ip: Optional[str] = None
    details: Dict = field(default_factory=dict)


class NetworkMonitor:
    """
    Passive network monitor with anomaly detection

    Features:
    - Device discovery through traffic analysis
    - Protocol identification
    - Baseline establishment
    - Anomaly detection
    - Statistics collection
    """

    def __init__(self):
        self.capture = SecurePacketCapture()
        self.is_monitoring = False

        # Device tracking
        self.devices: Dict[str, DeviceProfile] = {}
        self.device_lock = threading.Lock()

        # Traffic statistics
        self.protocol_stats = defaultdict(int)
        self.port_stats = defaultdict(int)
        self.connection_stats = defaultdict(int)

        # Baseline and anomaly detection
        self.baseline: Optional[TrafficBaseline] = None
        self.anomalies: deque = deque(maxlen=1000)
        self.learning_mode = True
        self.learning_start: Optional[datetime] = None

        # Time-series data for dashboard
        self.packet_history = deque(maxlen=300)  # 5 minutes at 1/sec
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize custom alert rules engine
        try:
            self.alert_rules_engine = AlertRulesEngine()
            summary = self.alert_rules_engine.get_rule_summary()
            self.logger.info(f"Custom alert rules loaded: {summary['enabled_rules']} rules enabled")
        except Exception as e:
            self.logger.warning(f"Could not load custom alert rules: {e}")
            self.alert_rules_engine = None
        self.protocol_history = deque(maxlen=60)  # 1 minute

        logger.info("NetworkMonitor initialized")

    def start_monitoring(self,
                         interface: Optional[str] = None,
                         duration: Optional[int] = None,
                         learn_baseline: bool = True):
        """Start network monitoring"""
        if self.is_monitoring:
            logger.warning("Monitoring already in progress")
            return False

        self.is_monitoring = True
        self.learning_mode = learn_baseline
        self.learning_start = datetime.now() if learn_baseline else None

        logger.info(f"Starting network monitor (learning_mode={learn_baseline})")

        # Start packet capture
        success = self.capture.start_capture(
            interface=interface,
            callback=self._process_packet,
            timeout=duration or 3600
        )

        if success:
            # Start statistics update thread
            self.stats_thread = threading.Thread(
                target=self._update_statistics,
                daemon=True
            )
            self.stats_thread.start()

        return success

    def stop_monitoring(self):
        """Stop network monitoring"""
        logger.info("Stopping network monitor")
        self.is_monitoring = False
        self.capture.stop_capture()

        # Generate baseline if in learning mode
        if self.learning_mode:
            self._generate_baseline()

    def _process_packet(self, packet: PacketInfo):
        """Process captured packet"""
        try:
            # Update device profiles
            with self.device_lock:
                # Source device
                if packet.src_ip not in self.devices:
                    self.devices[packet.src_ip] = DeviceProfile(ip_address=packet.src_ip)
                    self._check_new_device_anomaly(packet.src_ip)

                self.devices[packet.src_ip].update(packet)

                if packet.src_port:
                    self.devices[packet.src_ip].ports.add(packet.src_port)

                # Destination device
                if packet.dst_ip not in self.devices:
                    self.devices[packet.dst_ip] = DeviceProfile(ip_address=packet.dst_ip)
                    self._check_new_device_anomaly(packet.dst_ip)

                # Track connection
                connection = f"{packet.src_ip}:{packet.src_port}->{packet.dst_ip}:{packet.dst_port}"
                self.devices[packet.src_ip].connections.add(connection)

            # Update statistics
            self.protocol_stats[packet.protocol] += 1
            self.port_stats[packet.dst_port] += 1
            self.connection_stats[connection] += 1

            # Anomaly detection (if not in learning mode)
            if not self.learning_mode and self.baseline:
                self._detect_anomalies(packet)

        except Exception as e:
            logger.error(f"Error processing packet: {e}")

    def _update_statistics(self):
        """Update time-series statistics for dashboard"""
        while self.is_monitoring:
            try:
                # Get current packet count
                stats = self.capture.get_statistics()

                # Add to history
                self.packet_history.append({
                    'timestamp': datetime.now(),
                    'packets': stats['packets_captured'],
                    'dropped': stats['packets_dropped']
                })

                # Protocol snapshot
                self.protocol_history.append({
                    'timestamp': datetime.now(),
                    'protocols': dict(self.protocol_stats)
                })

                time.sleep(1)  # Update every second

            except Exception as e:
                logger.error(f"Error updating statistics: {e}")

    def _generate_baseline(self):
        """Generate traffic baseline from learning period"""
        if not self.learning_start:
            return

        duration = (datetime.now() - self.learning_start).total_seconds() / 60

        if duration < 1:
            logger.warning("Learning period too short to generate baseline")
            return

        total_packets = sum(d.packet_count for d in self.devices.values())
        total_bytes = sum(d.byte_count for d in self.devices.values())

        self.baseline = TrafficBaseline(
            avg_packets_per_minute=total_packets / duration,
            avg_bytes_per_minute=total_bytes / duration,
            common_protocols=set(p for p, count in self.protocol_stats.items() if count > 10),
            common_ports=set(p for p, count in self.port_stats.items() if count > 5),
            typical_connections=set(c for c, count in self.connection_stats.items() if count > 3)
        )

        logger.info(f"Baseline generated: {self.baseline.avg_packets_per_minute:.1f} pkt/min, "
                    f"{len(self.baseline.common_protocols)} protocols")

    def _check_new_device_anomaly(self, ip: str):
        """Check if new device is anomalous and trigger alert"""
        if not self.learning_mode:
            anomaly = Anomaly(
                timestamp=datetime.now(),
                severity='HIGH',  # Elevated to HIGH for security awareness
                category='NEW_DEVICE',
                description=f"🆕 NEW DEVICE CONNECTED: {ip} - Not in baseline, requires investigation",
                source_ip=ip,
                details={
                    'action_required': 'Verify device authorization and add to asset inventory',
                    'recommendation': 'Investigate immediately if unauthorized'
                }
            )
            self.anomalies.append(anomaly)
            logger.warning(f"⚠️ SECURITY ALERT: New device detected on network: {ip}")
            logger.info(f"Action Required: Verify if device {ip} is authorized")

    def _detect_anomalies(self, packet: PacketInfo):
        """Detect anomalies in packet with enhanced IPS capabilities"""
        if not self.baseline:
            return

        # IPS: Detect potential attack patterns
        self._detect_attack_patterns(packet)

        # Evaluate custom alert rules first
        if hasattr(self, 'alert_rules_engine') and self.alert_rules_engine and self.alert_rules_engine.enabled:
            packet_data = {
                'src_ip': packet.src_ip,
                'dst_ip': packet.dst_ip,
                'src_port': packet.src_port,
                'dst_port': packet.dst_port,
                'protocol': packet.protocol
            }

            custom_alerts = self.alert_rules_engine.evaluate_packet(packet_data)

            # Convert custom alerts to Anomaly objects
            for alert in custom_alerts:
                anomaly = Anomaly(
                    timestamp=datetime.now(),
                    severity=alert['severity'],
                    category=alert['category'],
                    description=f"{alert['rule_name']}: {alert['description']}",
                    source_ip=alert['source_ip'],
                    details={
                        'rule_id': alert['rule_id'],
                        'dest_ip': alert['dest_ip'],
                        'dest_port': alert['dest_port']
                    }
                )
                self.anomalies.append(anomaly)

        # Check for unusual protocol
        if packet.protocol not in self.baseline.common_protocols:
            # Ignore if it's a known industrial protocol
            industrial_protocols = ['Modbus/TCP', 'DNP3', 'OPC UA', 'S7comm', 'EtherNet/IP']

            if packet.protocol in industrial_protocols:
                severity = 'HIGH'
                description = f"⚠️ Unexpected industrial protocol detected: {packet.protocol}"
            else:
                severity = 'LOW'
                description = f"Unusual protocol detected: {packet.protocol}"

            anomaly = Anomaly(
                timestamp=datetime.now(),
                severity=severity,
                category='UNUSUAL_PROTOCOL',
                description=description,
                source_ip=packet.src_ip,
                details={
                    'protocol': packet.protocol,
                    'dst_ip': packet.dst_ip,
                    'dst_port': packet.dst_port
                }
            )
            self.anomalies.append(anomaly)

        # Check for unusual port
        if packet.dst_port not in self.baseline.common_ports:
            if packet.dst_port in [502, 20000, 4840, 102, 44818]:  # Industrial ports
                anomaly = Anomaly(
                    timestamp=datetime.now(),
                    severity='HIGH',
                    category='UNUSUAL_PORT',
                    description=f"🚨 Traffic to industrial port {packet.dst_port} ({packet.protocol})",
                    source_ip=packet.src_ip,
                    details={
                        'port': packet.dst_port,
                        'protocol': packet.protocol,
                        'dst_ip': packet.dst_ip
                    }
                )
                self.anomalies.append(anomaly)

    def _detect_attack_patterns(self, packet: PacketInfo):
        """Detect common attack patterns (IPS functionality)"""

        # Track packet rates per source IP for rate-based attacks
        if not hasattr(self, '_packet_rate_tracker'):
            self._packet_rate_tracker = defaultdict(lambda: {'count': 0, 'last_reset': datetime.now()})

        src_ip = packet.src_ip
        tracker = self._packet_rate_tracker[src_ip]

        # Reset counter every minute
        if (datetime.now() - tracker['last_reset']).total_seconds() > 60:
            tracker['count'] = 0
            tracker['last_reset'] = datetime.now()

        tracker['count'] += 1

        # 1. Port Scanning Detection (high rate of connections to different ports)
        if tracker['count'] > 100:  # More than 100 packets per minute from single source
            anomaly = Anomaly(
                timestamp=datetime.now(),
                severity='CRITICAL',
                category='PORT_SCAN',
                description=f"🚨 ATTACK DETECTED: Potential port scanning from {src_ip}",
                source_ip=src_ip,
                details={
                    'packet_rate': tracker['count'],
                    'attack_type': 'Port Scan / Network Reconnaissance',
                    'action': 'BLOCK recommended - Add firewall rule to block this IP'
                }
            )
            self.anomalies.append(anomaly)
            logger.critical(f"🚨 IPS ALERT: Port scanning detected from {src_ip}")

        # 2. Brute Force Attack Detection (multiple attempts to authentication ports)
        auth_ports = {22, 23, 3389, 5900, 21, 445}  # SSH, Telnet, RDP, VNC, FTP, SMB
        if packet.dst_port in auth_ports:
            if not hasattr(self, '_auth_attempt_tracker'):
                self._auth_attempt_tracker = defaultdict(lambda: {'count': 0, 'last_reset': datetime.now()})

            auth_tracker = self._auth_attempt_tracker[src_ip]
            if (datetime.now() - auth_tracker['last_reset']).total_seconds() > 60:
                auth_tracker['count'] = 0
                auth_tracker['last_reset'] = datetime.now()

            auth_tracker['count'] += 1

            if auth_tracker['count'] > 20:  # More than 20 auth attempts per minute
                anomaly = Anomaly(
                    timestamp=datetime.now(),
                    severity='CRITICAL',
                    category='BRUTE_FORCE',
                    description=f"🚨 ATTACK DETECTED: Brute force attack from {src_ip} targeting port {packet.dst_port}",
                    source_ip=src_ip,
                    details={
                        'target_port': packet.dst_port,
                        'target_ip': packet.dst_ip,
                        'attempt_count': auth_tracker['count'],
                        'attack_type': 'Credential Brute Force',
                        'action': 'BLOCK IMMEDIATELY - Attackingin progress'
                    }
                )
                self.anomalies.append(anomaly)
                logger.critical(f"🚨 IPS ALERT: Brute force attack detected from {src_ip} on port {packet.dst_port}")

        # 3. OT/ICS Protocol Attack Detection
        ot_attack_ports = {502, 102, 44818, 2222, 20000, 4840}  # Modbus, S7, EIP, DNP3, OPC-UA
        if packet.dst_port in ot_attack_ports:
            anomaly = Anomaly(
                timestamp=datetime.now(),
                severity='CRITICAL',
                category='OT_ATTACK',
                description=f"🚨 CRITICAL: OT/ICS protocol access from {src_ip} to {packet.dst_ip}:{packet.dst_port}",
                source_ip=src_ip,
                details={
                    'target_port': packet.dst_port,
                    'target_device': packet.dst_ip,
                    'protocol': 'OT/ICS',
                    'attack_type': 'Industrial Control System Intrusion',
                    'action': 'INVESTIGATE IMMEDIATELY - Potential sabotage attempt'
                }
            )
            self.anomalies.append(anomaly)
            logger.critical(f"🚨 IPS ALERT: OT protocol access from {src_ip} to critical port {packet.dst_port}")

        # 4. DoS/DDoS Detection (extremely high packet rate)
        if tracker['count'] > 500:  # More than 500 packets per minute
            anomaly = Anomaly(
                timestamp=datetime.now(),
                severity='CRITICAL',
                category='DOS_ATTACK',
                description=f"🚨 ATTACK DETECTED: Potential DoS/DDoS attack from {src_ip}",
                source_ip=src_ip,
                details={
                    'packet_rate': tracker['count'],
                    'attack_type': 'Denial of Service (DoS)',
                    'action': 'BLOCK IMMEDIATELY - Network flooding detected'
                }
            )
            self.anomalies.append(anomaly)
            logger.critical(f"🚨 IPS ALERT: DoS attack detected from {src_ip}")

        # 5. Malware C2 Communication Detection (unusual external connections)
        if not hasattr(self, '_known_external_ips'):
            self._known_external_ips = set()

        # Check if destination is external (simplified check)
        if not packet.dst_ip.startswith('192.168.') and not packet.dst_ip.startswith('10.') and not packet.dst_ip.startswith('172.'):
            if packet.dst_ip not in self._known_external_ips:
                self._known_external_ips.add(packet.dst_ip)
                anomaly = Anomaly(
                    timestamp=datetime.now(),
                    severity='HIGH',
                    category='EXTERNAL_CONNECTION',
                    description=f"⚠️ Suspicious external connection from {src_ip} to {packet.dst_ip}:{packet.dst_port}",
                    source_ip=src_ip,
                    details={
                        'external_ip': packet.dst_ip,
                        'port': packet.dst_port,
                        'attack_type': 'Possible Malware C2 Communication',
                        'action': 'Investigate source device for malware'
                    }
                )
                self.anomalies.append(anomaly)
                logger.warning(f"⚠️ IPS ALERT: External connection from {src_ip} to {packet.dst_ip}")

    def get_discovered_devices(self) -> List[Dict]:
        """Get list of discovered devices"""
        with self.device_lock:
            devices = []
            for ip, profile in self.devices.items():
                devices.append({
                    'ip_address': ip,
                    'mac_address': profile.mac_address,
                    'first_seen': profile.first_seen.isoformat(),
                    'last_seen': profile.last_seen.isoformat(),
                    'protocols': list(profile.protocols),
                    'ports': sorted(list(profile.ports)),
                    'packet_count': profile.packet_count,
                    'byte_count': profile.byte_count,
                    'connection_count': len(profile.connections)
                })
            return devices

    def get_new_devices_for_inventory(self, since_minutes: int = 5) -> List[Dict]:
        """Get newly discovered devices for automatic asset inventory addition

        Args:
            since_minutes: Get devices discovered within last N minutes

        Returns:
            List of device dictionaries suitable for asset inventory
        """
        cutoff_time = datetime.now() - timedelta(minutes=since_minutes)
        new_devices = []

        with self.device_lock:
            for ip, profile in self.devices.items():
                # Only include devices discovered after cutoff time
                if profile.first_seen > cutoff_time:
                    # Determine if it's an OT device based on ports
                    ot_ports = {502, 44818, 2222, 102, 20000, 4840, 47808, 1911, 789, 5094}
                    is_ot = bool(profile.ports & ot_ports)

                    device_info = {
                        'ip': ip,
                        'hostname': ip,  # Will be enriched by asset manager
                        'mac_address': profile.mac_address or 'Unknown',
                        'status': 'online',
                        'first_seen': profile.first_seen.isoformat(),
                        'last_seen': profile.last_seen.isoformat(),
                        'protocols': list(profile.protocols),
                        'open_ports': sorted(list(profile.ports)),
                        'is_ot_device': is_ot,
                        'packet_count': profile.packet_count,
                        'byte_count': profile.byte_count,
                        'source': 'live_monitoring',
                        'auto_discovered': True
                    }
                    new_devices.append(device_info)

        return new_devices

    def get_protocol_statistics(self) -> Dict:
        """Get protocol statistics"""
        total = sum(self.protocol_stats.values())

        stats = {
            'total_packets': total,
            'protocols': []
        }

        for protocol, count in sorted(self.protocol_stats.items(),
                                      key=lambda x: x[1], reverse=True):
            stats['protocols'].append({
                'name': protocol,
                'count': count,
                'percentage': (count / total * 100) if total > 0 else 0
            })

        return stats

    def get_recent_anomalies(self, minutes: int = 5) -> List[Anomaly]:
        """Get recent anomalies"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [a for a in self.anomalies if a.timestamp > cutoff]

    def get_dashboard_data(self) -> Dict:
        """Get data for live dashboard"""
        stats = self.capture.get_statistics()

        return {
            'is_monitoring': self.is_monitoring,
            'learning_mode': self.learning_mode,
            'packets_captured': stats['packets_captured'],
            'packets_dropped': stats['packets_dropped'],
            'devices_discovered': len(self.devices),
            'protocols': self.get_protocol_statistics(),
            'recent_anomalies': [
                {
                    'timestamp': a.timestamp.isoformat(),
                    'severity': a.severity,
                    'category': a.category,
                    'description': a.description,
                    'source_ip': a.source_ip
                }
                for a in self.get_recent_anomalies()
            ],
            'packet_history': list(self.packet_history),
            'baseline': {
                'packets_per_minute': self.baseline.avg_packets_per_minute if self.baseline else 0,
                'bytes_per_minute': self.baseline.avg_bytes_per_minute if self.baseline else 0,
                'protocols': list(self.baseline.common_protocols) if self.baseline else []
            } if self.baseline else None
        }



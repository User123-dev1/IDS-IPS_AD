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
        """Check if new device is anomalous"""
        if not self.learning_mode:
            anomaly = Anomaly(
                timestamp=datetime.now(),
                severity='MEDIUM',
                category='NEW_DEVICE',
                description=f"New device detected on network: {ip}",
                source_ip=ip
            )
            self.anomalies.append(anomaly)
            logger.warning(f"Anomaly detected: New device {ip}")

    def _detect_anomalies(self, packet: PacketInfo):
        """Detect anomalies in packet"""
        if not self.baseline:
            return

        # Check for unusual protocol
        if packet.protocol not in self.baseline.common_protocols:
            # Ignore if it's a known industrial protocol
            industrial_protocols = ['Modbus/TCP', 'DNP3', 'OPC UA', 'S7comm', 'EtherNet/IP']

            if packet.protocol in industrial_protocols:
                severity = 'HIGH'
                description = f"Unexpected industrial protocol detected: {packet.protocol}"
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
                    description=f"Traffic to industrial port {packet.dst_port} ({packet.protocol})",
                    source_ip=packet.src_ip,
                    details={
                        'port': packet.dst_port,
                        'protocol': packet.protocol,
                        'dst_ip': packet.dst_ip
                    }
                )
                self.anomalies.append(anomaly)

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

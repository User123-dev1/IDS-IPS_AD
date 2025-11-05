"""
Industrial Protocol Analyzer
Analyzes OT/ICS protocols: Modbus, EtherNet/IP, S7comm, DNP3, BACnet, OPC UA
"""

import socket
import struct
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO)


@dataclass
class ProtocolInfo:
    """Information about a detected protocol"""
    protocol_name: str
    port: int
    device_ip: str
    device_hostname: str
    status: str  # Active, Detected, Inactive
    vendor: str
    protocol_version: str
    details: Dict
    security_issues: List[str]
    timestamp: datetime


class IndustrialProtocolAnalyzer:
    """
    Analyzes industrial/OT protocols on discovered devices
    """

    # Protocol definitions
    INDUSTRIAL_PROTOCOLS = {
        'Modbus TCP': {
            'port': 502,
            'description': 'Modbus TCP/IP Protocol',
            'category': 'Industrial',
            'risk_level': 'High',
            'common_devices': ['PLC', 'RTU', 'HMI']
        },
        'EtherNet/IP': {
            'port': 44818,
            'description': 'EtherNet/IP (CIP over Ethernet)',
            'category': 'Industrial',
            'risk_level': 'High',
            'common_devices': ['PLC', 'Drive', 'I/O Module']
        },
        'S7comm': {
            'port': 102,
            'description': 'Siemens S7 Communication',
            'category': 'Industrial',
            'risk_level': 'Critical',
            'common_devices': ['Siemens PLC', 'HMI']
        },
        'DNP3': {
            'port': 20000,
            'description': 'Distributed Network Protocol 3',
            'category': 'SCADA',
            'risk_level': 'High',
            'common_devices': ['RTU', 'IED', 'SCADA Master']
        },
        'IEC 60870-5-104': {
            'port': 2404,
            'description': 'IEC 104 Protocol',
            'category': 'SCADA',
            'risk_level': 'High',
            'common_devices': ['RTU', 'Substation', 'SCADA']
        },
        'BACnet': {
            'port': 47808,
            'description': 'Building Automation Protocol',
            'category': 'Building Automation',
            'risk_level': 'Medium',
            'common_devices': ['HVAC', 'BMS', 'Controller']
        },
        'OPC UA': {
            'port': 4840,
            'description': 'OPC Unified Architecture',
            'category': 'Industrial',
            'risk_level': 'Medium',
            'common_devices': ['PLC', 'HMI', 'SCADA']
        },
        'OMRON FINS': {
            'port': 9600,
            'description': 'OMRON FINS Protocol',
            'category': 'Industrial',
            'risk_level': 'High',
            'common_devices': ['OMRON PLC']
        }
    }

    def __init__(self):
        self.discovered_protocols: List[ProtocolInfo] = []
        logging.info("Industrial Protocol Analyzer initialized")

    def analyze_devices(self, devices: List[Dict]) -> List[ProtocolInfo]:
        """
        Analyze all devices for industrial protocols

        Args:
            devices: List of discovered devices from network scanner

        Returns:
            List of detected protocols
        """
        self.discovered_protocols = []

        for device in devices:
            ip = device.get('ip_address', '')
            hostname = device.get('hostname', '')
            open_ports = device.get('open_ports', [])
            device_type = device.get('device_type', '')
            vendor = device.get('vendor', 'Unknown')

            # Check each open port for known industrial protocols
            for port in open_ports:
                protocol_info = self._identify_protocol(port, ip, hostname, device_type, vendor)
                if protocol_info:
                    self.discovered_protocols.append(protocol_info)

        logging.info(f"Protocol analysis complete: {len(self.discovered_protocols)} protocols found")
        return self.discovered_protocols

    def _identify_protocol(self, port: int, ip: str, hostname: str,
                           device_type: str, vendor: str) -> Optional[ProtocolInfo]:
        """Identify protocol on specific port"""

        # Find matching protocol
        for protocol_name, protocol_data in self.INDUSTRIAL_PROTOCOLS.items():
            if protocol_data['port'] == port:
                # Perform protocol-specific detection
                details = self._probe_protocol(protocol_name, ip, port)

                # Check for security issues
                security_issues = self._check_protocol_security(protocol_name, details)

                return ProtocolInfo(
                    protocol_name=protocol_name,
                    port=port,
                    device_ip=ip,
                    device_hostname=hostname,
                    status='Active' if details.get('responds', False) else 'Detected',
                    vendor=vendor,
                    protocol_version=details.get('version', 'Unknown'),
                    details=details,
                    security_issues=security_issues,
                    timestamp=datetime.now()
                )

        return None

    def _probe_protocol(self, protocol_name: str, ip: str, port: int) -> Dict:
        """
        Probe specific protocol for details
        """
        details = {
            'responds': False,
            'version': 'Unknown',
            'features': [],
            'response_time': None
        }

        try:
            # Protocol-specific probing
            if protocol_name == 'Modbus TCP':
                details = self._probe_modbus(ip, port)
            elif protocol_name == 'S7comm':
                details = self._probe_s7comm(ip, port)
            elif protocol_name == 'EtherNet/IP':
                details = self._probe_ethernetip(ip, port)
            elif protocol_name == 'DNP3':
                details = self._probe_dnp3(ip, port)
            elif protocol_name == 'OPC UA':
                details = self._probe_opcua(ip, port)
            else:
                # Generic TCP probe
                details = self._generic_tcp_probe(ip, port)

        except Exception as e:
            logging.debug(f"Error probing {protocol_name} on {ip}:{port} - {e}")

        return details

    def _probe_modbus(self, ip: str, port: int) -> Dict:
        """Probe Modbus TCP protocol"""
        details = {
            'responds': False,
            'version': 'Modbus TCP',
            'features': ['Read Coils', 'Read Registers'],
            'response_time': None,
            'unit_id': 1
        }

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)

            start_time = datetime.now()
            sock.connect((ip, port))

            # Modbus TCP Read Holding Registers request (Function Code 03)
            # Transaction ID: 0001, Protocol: 0000, Length: 0006, Unit ID: 01, FC: 03, Start: 0000, Quantity: 0001
            modbus_request = bytes([0x00, 0x01, 0x00, 0x00, 0x00, 0x06, 0x01, 0x03, 0x00, 0x00, 0x00, 0x01])

            sock.send(modbus_request)
            response = sock.recv(1024)

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            if len(response) > 0:
                details['responds'] = True
                details['response_time'] = f"{response_time:.2f}ms"
                details['features'].append('Function Code 03 supported')

            sock.close()

        except Exception as e:
            logging.debug(f"Modbus probe failed for {ip}:{port} - {e}")

        return details

    def _probe_s7comm(self, ip: str, port: int) -> Dict:
        """Probe Siemens S7comm protocol"""
        details = {
            'responds': False,
            'version': 'S7-300/400',
            'features': [],
            'response_time': None,
            'plc_type': 'Unknown'
        }

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)

            start_time = datetime.now()
            sock.connect((ip, port))

            # S7comm COTP Connection Request
            s7_cotp = bytes([
                0x03, 0x00, 0x00, 0x16,  # TPKT Header
                0x11, 0xe0, 0x00, 0x00, 0x00, 0x01, 0x00,
                0xc1, 0x02, 0x01, 0x00, 0xc2, 0x02, 0x01, 0x02,
                0xc0, 0x01, 0x0a
            ])

            sock.send(s7_cotp)
            response = sock.recv(1024)

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            if len(response) > 0:
                details['responds'] = True
                details['response_time'] = f"{response_time:.2f}ms"
                details['features'].append('COTP Connection established')

            sock.close()

        except Exception as e:
            logging.debug(f"S7comm probe failed for {ip}:{port} - {e}")

        return details

    def _probe_ethernetip(self, ip: str, port: int) -> Dict:
        """Probe EtherNet/IP protocol"""
        details = {
            'responds': False,
            'version': 'EtherNet/IP',
            'features': ['CIP', 'Implicit Messaging'],
            'response_time': None
        }

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)

            start_time = datetime.now()
            sock.connect((ip, port))

            # EtherNet/IP List Identity request
            enip_request = bytes([
                0x63, 0x00,  # Command: ListIdentity
                0x00, 0x00,  # Length
                0x00, 0x00, 0x00, 0x00,  # Session handle
                0x00, 0x00, 0x00, 0x00,  # Status
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Sender context
                0x00, 0x00, 0x00, 0x00  # Options
            ])

            sock.send(enip_request)
            response = sock.recv(1024)

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            if len(response) > 0:
                details['responds'] = True
                details['response_time'] = f"{response_time:.2f}ms"
                details['features'].append('ListIdentity supported')

            sock.close()

        except Exception as e:
            logging.debug(f"EtherNet/IP probe failed for {ip}:{port} - {e}")

        return details

    def _probe_dnp3(self, ip: str, port: int) -> Dict:
        """Probe DNP3 protocol"""
        details = {
            'responds': False,
            'version': 'DNP3',
            'features': ['Master/Outstation'],
            'response_time': None
        }

        return self._generic_tcp_probe(ip, port)

    def _probe_opcua(self, ip: str, port: int) -> Dict:
        """Probe OPC UA protocol"""
        details = {
            'responds': False,
            'version': 'OPC UA',
            'features': ['Pub/Sub', 'Client/Server'],
            'response_time': None
        }

        return self._generic_tcp_probe(ip, port)

    def _generic_tcp_probe(self, ip: str, port: int) -> Dict:
        """Generic TCP connection test"""
        details = {
            'responds': False,
            'version': 'Unknown',
            'features': [],
            'response_time': None
        }

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)

            start_time = datetime.now()
            result = sock.connect_ex((ip, port))
            response_time = (datetime.now() - start_time).total_seconds() * 1000

            if result == 0:
                details['responds'] = True
                details['response_time'] = f"{response_time:.2f}ms"

            sock.close()

        except Exception as e:
            logging.debug(f"TCP probe failed for {ip}:{port} - {e}")

        return details

    def _check_protocol_security(self, protocol_name: str, details: Dict) -> List[str]:
        """Check for common security issues"""
        issues = []

        # Common OT protocol security issues
        security_checks = {
            'Modbus TCP': [
                'No authentication required',
                'Plain text communication',
                'Susceptible to replay attacks'
            ],
            'S7comm': [
                'No authentication in legacy versions',
                'Plain text communication',
                'Direct PLC access possible'
            ],
            'EtherNet/IP': [
                'Limited authentication',
                'Plain text communication',
                'CIP security not always enabled'
            ],
            'DNP3': [
                'Weak authentication in DNP3 Secure Auth v2',
                'Plain text communication',
                'Susceptible to man-in-the-middle'
            ],
            'IEC 60870-5-104': [
                'No encryption by default',
                'Weak authentication',
                'Plain text communication'
            ]
        }

        if protocol_name in security_checks:
            issues = security_checks[protocol_name]

        # Add generic issues
        if not details.get('encrypted', False):
            issues.append('Unencrypted communication')

        return issues

    def get_protocol_statistics(self) -> Dict:
        """Get statistics about discovered protocols"""
        stats = {
            'total_protocols': len(self.discovered_protocols),
            'active_protocols': sum(1 for p in self.discovered_protocols if p.status == 'Active'),
            'critical_count': 0,
            'high_risk_count': 0,
            'protocols_by_type': {},
            'devices_with_protocols': set()
        }

        for protocol in self.discovered_protocols:
            # Count by protocol type
            if protocol.protocol_name not in stats['protocols_by_type']:
                stats['protocols_by_type'][protocol.protocol_name] = 0
            stats['protocols_by_type'][protocol.protocol_name] += 1

            # Track unique devices
            stats['devices_with_protocols'].add(protocol.device_ip)

            # Count risk levels
            protocol_info = self.INDUSTRIAL_PROTOCOLS.get(protocol.protocol_name, {})
            risk = protocol_info.get('risk_level', 'Unknown')

            if risk == 'Critical':
                stats['critical_count'] += 1
            elif risk == 'High':
                stats['high_risk_count'] += 1

        stats['unique_devices'] = len(stats['devices_with_protocols'])
        del stats['devices_with_protocols']

        return stats

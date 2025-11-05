"""
Secure Packet Capture Module for OT Asset Manager
Implements defense-in-depth against packet parsing vulnerabilities

Security Features:
- Input validation and sanitization
- Resource limits (packet count, memory)
- Rate limiting to prevent DoS
- No execution of packet data
- Safe parsing with exception handling
- Privilege separation support
"""

import logging
import threading
import queue
import time
from datetime import datetime
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from collections import defaultdict

try:
    from scapy.all import sniff, IP, TCP, UDP, Raw, Ether
    from scapy.error import Scapy_Exception

    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("Warning: Scapy not available. Install with: pip install scapy")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PacketInfo:
    """Safe packet information container (no raw packet data stored)"""
    timestamp: datetime
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    size: int
    flags: str
    payload_preview: str  # Limited to 100 chars, sanitized


class SecurePacketCapture:
    """
    Secure packet capture with defense against parsing vulnerabilities
    """

    # Security limits
    MAX_PACKETS = 100000
    MAX_PACKET_SIZE = 65535
    MAX_QUEUE_SIZE = 10000
    MAX_PAYLOAD_PREVIEW = 100
    RATE_LIMIT = 10000

    # Industrial protocol ports
    INDUSTRIAL_PORTS = {
        502: 'Modbus/TCP',
        20000: 'DNP3',
        2404: 'IEC-104',
        44818: 'EtherNet/IP',
        102: 'S7comm',
        34962: 'Profinet DCP',
        34964: 'Profinet CM',
        9600: 'BACnet',
        47808: 'BACnet',
        1911: 'Niagara Fox',
        5094: 'PCWorx',
        789: 'Red Lion Crimson',
        4840: 'OPC UA',
    }

    def __init__(self):
        """Initialize secure packet capture"""
        if not SCAPY_AVAILABLE:
            raise ImportError("Scapy is required for packet capture")

        self.is_capturing = False
        self.packets_captured = 0
        self.packets_dropped = 0
        self.capture_thread = None
        self.packet_queue = queue.Queue(maxsize=self.MAX_QUEUE_SIZE)
        self.statistics = defaultdict(int)

        # Rate limiting
        self.last_rate_check = time.time()
        self.packets_this_second = 0

        logger.info("SecurePacketCapture initialized with safety limits")

    def start_capture(self,
                      interface: Optional[str] = None,
                      filter_expr: Optional[str] = None,
                      callback: Optional[Callable] = None,
                      timeout: int = 60):
        """Start secure packet capture"""
        if self.is_capturing:
            logger.warning("Capture already in progress")
            return False

        # Validate filter expression
        if filter_expr and not self._validate_bpf_filter(filter_expr):
            logger.error("Invalid BPF filter expression")
            return False

        self.is_capturing = True
        self.packets_captured = 0
        self.packets_dropped = 0

        # Start capture in separate thread
        self.capture_thread = threading.Thread(
            target=self._capture_worker,
            args=(interface, filter_expr, callback, timeout),
            daemon=True
        )
        self.capture_thread.start()

        logger.info(f"Packet capture started (interface={interface}, filter={filter_expr})")
        return True

    def stop_capture(self):
        """Stop packet capture"""
        self.is_capturing = False

        if self.capture_thread:
            self.capture_thread.join(timeout=5)

        logger.info(f"Capture stopped. Captured={self.packets_captured}, Dropped={self.packets_dropped}")

    def _capture_worker(self, interface, filter_expr, callback, timeout):
        """Worker thread for packet capture"""
        try:
            # Build safe filter
            safe_filter = self._build_industrial_filter(filter_expr)

            start_time = time.time()

            def packet_handler(packet):
                """Safe packet handler"""
                # Check timeout
                if time.time() - start_time > timeout:
                    self.is_capturing = False
                    return

                # Check packet limit
                if self.packets_captured >= self.MAX_PACKETS:
                    logger.warning("Maximum packet limit reached")
                    self.is_capturing = False
                    return

                # Rate limiting
                if not self._check_rate_limit():
                    self.packets_dropped += 1
                    return

                # Process packet safely
                packet_info = self._safe_parse_packet(packet)

                if packet_info:
                    self.packets_captured += 1

                    # Add to queue
                    try:
                        self.packet_queue.put_nowait(packet_info)
                    except queue.Full:
                        self.packets_dropped += 1

                    # Call user callback
                    if callback:
                        try:
                            callback(packet_info)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")

            # Start capture
            sniff(
                iface=interface,
                filter=safe_filter,
                prn=packet_handler,
                store=False,
                stop_filter=lambda x: not self.is_capturing
            )

        except Scapy_Exception as e:
            logger.error(f"Scapy error: {e}")
        except Exception as e:
            logger.error(f"Capture error: {e}")
        finally:
            self.is_capturing = False

    def _safe_parse_packet(self, packet) -> Optional[PacketInfo]:
        """Safely parse packet with validation"""
        try:
            if not packet.haslayer(IP):
                return None

            ip_layer = packet[IP]

            # Validate IPs
            src_ip = self._sanitize_ip(str(ip_layer.src))
            dst_ip = self._sanitize_ip(str(ip_layer.dst))

            if not src_ip or not dst_ip:
                return None

            # Get protocol and ports
            protocol = 'Unknown'
            src_port = 0
            dst_port = 0
            flags = ''

            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                protocol = 'TCP'
                src_port = self._sanitize_port(tcp_layer.sport)
                dst_port = self._sanitize_port(tcp_layer.dport)
                flags = self._get_tcp_flags(tcp_layer)

            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                protocol = 'UDP'
                src_port = self._sanitize_port(udp_layer.sport)
                dst_port = self._sanitize_port(udp_layer.dport)

            # Check if industrial protocol
            protocol_name = self.INDUSTRIAL_PORTS.get(dst_port, protocol)

            # Get packet size
            size = min(len(packet), self.MAX_PACKET_SIZE)

            # Get safe payload
            payload_preview = self._get_safe_payload(packet)

            # Update statistics
            self.statistics[protocol_name] += 1

            return PacketInfo(
                timestamp=datetime.now(),
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol=protocol_name,
                size=size,
                flags=flags,
                payload_preview=payload_preview
            )

        except Exception as e:
            logger.debug(f"Error parsing packet: {e}")
            return None

    def _sanitize_ip(self, ip: str) -> Optional[str]:
        """Validate and sanitize IP address"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return None

            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return None

            return ip
        except:
            return None

    def _sanitize_port(self, port: int) -> int:
        """Validate port number"""
        if 0 <= port <= 65535:
            return port
        return 0

    def _get_tcp_flags(self, tcp_layer) -> str:
        """Safely extract TCP flags"""
        flags = []
        try:
            if tcp_layer.flags.S: flags.append('SYN')
            if tcp_layer.flags.A: flags.append('ACK')
            if tcp_layer.flags.F: flags.append('FIN')
            if tcp_layer.flags.R: flags.append('RST')
            if tcp_layer.flags.P: flags.append('PSH')
        except:
            pass
        return ','.join(flags) if flags else ''

    def _get_safe_payload(self, packet) -> str:
        """Get sanitized payload preview"""
        try:
            if packet.haslayer(Raw):
                payload = bytes(packet[Raw].load)
                payload = payload[:self.MAX_PAYLOAD_PREVIEW]

                safe_payload = ''.join(
                    chr(b) if 32 <= b <= 126 else '.'
                    for b in payload
                )

                return safe_payload if safe_payload else '[Binary Data]'
        except:
            pass

        return ''

    def _check_rate_limit(self) -> bool:
        """Check if rate limit is exceeded"""
        current_time = time.time()

        if current_time - self.last_rate_check >= 1.0:
            self.last_rate_check = current_time
            self.packets_this_second = 0

        self.packets_this_second += 1

        return self.packets_this_second <= self.RATE_LIMIT

    def _validate_bpf_filter(self, filter_expr: str) -> bool:
        """Validate BPF filter expression"""
        if not filter_expr:
            return True


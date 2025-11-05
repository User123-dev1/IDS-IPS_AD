"""
Enterprise Network Scanner
Professional OT/IT Network Discovery Module
"""

import socket
import subprocess
import platform
import ipaddress
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class EnterpriseNetworkScanner:
    """
    Advanced network scanner for discovering OT/IT devices
    Supports multi-subnet scanning with device type identification
    """

    def __init__(self, max_workers: int = 50):
        """
        Initialize the network scanner

        Args:
            max_workers: Maximum number of concurrent scanning threads
        """
        self.max_workers = max_workers
        self.is_scanning = False
        logging.info(f"EnterpriseNetworkScanner initialized (max_workers={max_workers})")

    # ==========================================
    # PUBLIC METHODS
    # ==========================================

    def scan_multiple_subnets(self, subnets: List[str]) -> List[Dict]:
        """
        Scan multiple subnets and return all discovered devices

        Args:
            subnets: List of subnet strings in CIDR notation (e.g., ["192.168.1.0/24"])

        Returns:
            list: All discovered devices with their properties
        """
        self.is_scanning = True
        all_devices = []

        try:
            for subnet in subnets:
                logging.info(f"🔍 Scanning subnet: {subnet}")

                try:
                    # Generate all IP addresses in subnet
                    network = ipaddress.ip_network(subnet, strict=False)
                    ip_list = [str(ip) for ip in network.hosts()]

                    logging.info(f"   📊 {len(ip_list)} hosts to scan")

                    # Scan hosts in parallel using ThreadPoolExecutor
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        # Submit all scan jobs
                        future_to_ip = {
                            executor.submit(self._scan_host, ip): ip
                            for ip in ip_list
                        }

                        # Collect results
                        for future in as_completed(future_to_ip):
                            try:
                                device = future.result()
                                if device:  # Only add if device responded
                                    all_devices.append(device)
                                    logging.info(
                                        f"   ✅ Found: {device['ip_address']} "
                                        f"({device['device_type']}) - {device['hostname']}"
                                    )
                            except Exception as e:
                                logging.error(f"   ❌ Error processing scan result: {e}")

                except Exception as e:
                    logging.error(f"❌ Error scanning subnet {subnet}: {e}")

            logging.info(f"✅ Scan complete! Discovered {len(all_devices)} devices")

        finally:
            self.is_scanning = False

        return all_devices

    # ==========================================
    # HOST SCANNING
    # ==========================================

    def _scan_host(self, ip: str) -> Optional[Dict]:
        """
        Scan a single host and gather all information

        Returns:
            dict: Device information or None if host is unreachable
        """
        try:
            # 1. Check if host is alive (ping)
            if not self._is_host_alive(ip):
                return None

            # 2. Get hostname
            hostname = self._get_hostname(ip)

            # 3. Scan ports
            open_ports = self._scan_ports(ip)

            # 4. Get MAC address
            mac = self._get_mac_address(ip)

            # 5. Get vendor from MAC
            vendor = self._get_vendor_from_mac(mac)

            # 6. Identify device type
            device_type = self._identify_device_type(
                ip=ip,
                hostname=hostname,
                open_ports=open_ports,
                mac=mac,
                vendor=vendor
            )

            # 7. Detect services
            services = self._detect_services(ip, open_ports)

            # 8. Return device information
            return {
                'ip_address': ip,
                'hostname': hostname or ip,
                'mac': mac,
                'vendor': vendor,
                'device_type': device_type,
                'services': services,
                'status': 'online',
                'open_ports': open_ports
            }

        except Exception as e:
            logging.debug(f"Error scanning host {ip}: {e}")
            return None

    def _is_host_alive(self, ip: str) -> bool:
        """Check if host responds to ping"""
        try:
            # Ping command varies by OS
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'

            command = ['ping', param, '1', timeout_param, '1000' if platform.system().lower() == 'windows' else '1', ip]

            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2
            )
            return result.returncode == 0

        except Exception:
            # If ping fails, assume host might be alive (firewall blocking ICMP)
            return True

    def _get_hostname(self, ip: str) -> str:
        """Resolve hostname from IP"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return ""

    def _scan_ports(self, ip: str, ports: List[int] = None) -> List[int]:
        """
        Scan common ports on a host

        Args:
            ip: Target IP address
            ports: List of ports to scan (None = common ports)

        Returns:
            list: Open ports
        """
        if ports is None:
            # Common OT/IT ports
            ports = [
                21,    # FTP
                22,    # SSH
                23,    # Telnet
                25,    # SMTP
                53,    # DNS
                80,    # HTTP
                88,    # Kerberos
                102,   # S7comm (Siemens)
                110,   # POP3
                139,   # NetBIOS
                143,   # IMAP
                179,   # BGP
                389,   # LDAP
                443,   # HTTPS
                445,   # SMB
                502,   # Modbus TCP
                631,   # IPP (Printing)
                1433,  # MSSQL
                2222,  # EtherNet/IP
                2404,  # IEC 60870-5-104
                3306,  # MySQL
                3389,  # RDP
                5432,  # PostgreSQL
                5900,  # VNC
                8080,  # HTTP-Alt
                8443,  # HTTPS-Alt
                9100,  # JetDirect (Printing)
                9600,  # OMRON FINS
                20000, # DNP3
                44818, # EtherNet/IP
                47808  # BACnet
            ]

        open_ports = []

        try:
            for port in ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.3)  # Fast timeout
                    result = sock.connect_ex((ip, port))

                    if result == 0:
                        open_ports.append(port)

                    sock.close()

                except Exception:
                    continue

        except Exception as e:
            logging.debug(f"Port scan error for {ip}: {e}")

        return open_ports

    def _get_mac_address(self, ip: str) -> str:
        """
        Get MAC address for an IP (works on local network)

        Returns:
            str: MAC address in format XX:XX:XX:XX:XX:XX
        """
        try:
            if platform.system().lower() == 'windows':
                # Windows: use arp -a
                result = subprocess.check_output(
                    f'arp -a {ip}',
                    shell=True,
                    timeout=2
                ).decode('utf-8', errors='ignore')

                # Parse MAC from output
                mac_pattern = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
                match = re.search(mac_pattern, result)

                if match:
                    return match.group(0).replace('-', ':').upper()

            else:
                # Linux/Mac: use arp -n
                result = subprocess.check_output(
                    f'arp -n {ip}',
                    shell=True,
                    timeout=2
                ).decode('utf-8', errors='ignore')

                mac_pattern = r'([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}'
                match = re.search(mac_pattern, result)

                if match:
                    return match.group(0).upper()

        except Exception as e:
            logging.debug(f"Could not get MAC for {ip}: {e}")

        return ""

    # ==========================================
    # DEVICE IDENTIFICATION
    # ==========================================

    def _identify_device_type(self, ip: str, hostname: str, open_ports: List[int],
                             mac: str = None, vendor: str = None) -> str:
        """
        Enhanced device type identification based on multiple factors
        """
        hostname_lower = hostname.lower() if hostname else ""
        vendor_lower = vendor.lower() if vendor else ""

        # ==========================================
        # 1. INDUSTRIAL/OT DEVICES (Priority)
        # ==========================================

        # PLC Detection
        if any(port in open_ports for port in [502, 44818, 2222, 20000]):
            return "PLC"

        if any(keyword in hostname_lower for keyword in ['plc', 'controllogix', 'compactlogix', 'siemens', 's7-']):
            return "PLC"

        if any(keyword in vendor_lower for keyword in ['rockwell', 'allen-bradley', 'siemens', 'schneider']):
            return "PLC"

        # HMI/SCADA Detection
        if any(port in open_ports for port in [2404, 5900, 5800]):
            return "HMI"

        if any(keyword in hostname_lower for keyword in ['hmi', 'scada', 'operator', 'panelview']):
            return "HMI"

        # RTU Detection
        if any(port in open_ports for port in [20000, 2404]):
            return "RTU"

        if any(keyword in hostname_lower for keyword in ['rtu', 'remote-terminal']):
            return "RTU"

        # VFD/Drive Detection
        if any(keyword in hostname_lower for keyword in ['drive', 'vfd', 'inverter', 'powerflex']):
            return "VFD"

        # ==========================================
        # 2. NETWORK INFRASTRUCTURE
        # ==========================================

        # Router Detection
        if any(keyword in hostname_lower for keyword in ['router', 'gateway', 'rt-', 'rtr-', 'gw-', 'c892', 'tmo-']):
            return "Router"

        if any(keyword in vendor_lower for keyword in ['cisco', 'juniper', 'mikrotik', 't-mobile']) and 'switch' not in hostname_lower:
            return "Router"

        if 179 in open_ports:  # BGP
            return "Router"

        # Switch Detection
        if any(keyword in hostname_lower for keyword in ['switch', 'sw-', 'catalyst', 'nexus']):
            return "Switch"

        if any(keyword in vendor_lower for keyword in ['cisco', 'hp', 'aruba', 'juniper']) and any(
            keyword in hostname_lower for keyword in ['sw', 'switch', '2960', '3850', 'catalyst']
        ):
            return "Switch"

        # Firewall Detection
        if any(keyword in hostname_lower for keyword in ['firewall', 'fw-', 'fortigate', 'palo-alto', 'checkpoint']):
            return "Firewall"

        if any(keyword in vendor_lower for keyword in ['fortinet', 'paloalto', 'checkpoint', 'cisco asa']):
            return "Firewall"

        # ==========================================
        # 3. SERVERS & WORKSTATIONS
        # ==========================================

        # Domain Controller
        if 389 in open_ports and 88 in open_ports:  # LDAP + Kerberos
            return "Domain Controller"

        # Web Server
        if any(port in open_ports for port in [80, 443, 8080, 8443]):
            if any(port in open_ports for port in [3306, 5432, 1433]):
                return "Application Server"
            if any(keyword in hostname_lower for keyword in ['web', 'www', 'apache', 'nginx']):
                return "Web Server"

        # Database Server
        if any(port in open_ports for port in [3306, 5432, 1433, 27017]):
            return "Database Server"

        # File Server
        if any(port in open_ports for port in [445, 139, 2049]):
            if any(keyword in hostname_lower for keyword in ['file', 'nas', 'storage']):
                return "File Server"

        # Printer
        if 9100 in open_ports or 631 in open_ports:
            return "Printer"

        if any(keyword in hostname_lower for keyword in ['print', 'xerox', 'xrx', 'hp-', 'canon']):
            return "Printer"

        if any(keyword in vendor_lower for keyword in ['xerox', 'hewlett', 'canon', 'brother']):
            return "Printer"

        # Windows Workstation/Server
        if 445 in open_ports and 3389 in open_ports:
            if any(keyword in hostname_lower for keyword in ['pc-', 'ws-', 'desktop', 'laptop', 'home-', 'user-']):
                return "Workstation"
            return "Windows Server"

        if 445 in open_ports or 139 in open_ports:
            if any(keyword in hostname_lower for keyword in ['home-', 'pc-', 'desktop']):
                return "Workstation"

        # Linux Server
        if 22 in open_ports:
            if any(keyword in hostname_lower for keyword in ['server', 'srv-', 'node', 'host', 'research']):
                return "Linux Server"
            if any(keyword in hostname_lower for keyword in ['pc', 'desktop', 'laptop']):
                return "Linux Workstation"

        # ==========================================
        # 4. IoT & SPECIALTY DEVICES
        # ==========================================

        # IP Camera
        if any(port in open_ports for port in [554, 8000, 8080]) and any(
            keyword in hostname_lower for keyword in ['camera', 'cam-', 'ipcam', 'nvr', 'dvr']
        ):
            return "IP Camera"

        if any(keyword in vendor_lower for keyword in ['hikvision', 'dahua', 'axis']):
            return "IP Camera"

        # Access Control
        if any(keyword in hostname_lower for keyword in ['access', 'badge', 'card-reader']):
            return "Access Control"

        # Environmental Sensor
        if any(keyword in hostname_lower for keyword in ['sensor', 'temp', 'humidity', 'environmental']):
            return "Sensor"

        # UPS
        if 161 in open_ports and any(keyword in hostname_lower for keyword in ['ups', 'power']):
            return "UPS"

        # ==========================================
        # 5. DEFAULT CLASSIFICATIONS
        # ==========================================

        # Numeric hostname (likely generic device)
        if hostname and hostname.isdigit():
            if len(open_ports) > 0:
                return "Network Device"
            return "Unknown"

        # Generic classifications
        if len(open_ports) > 10:
            return "Server"
        elif len(open_ports) > 3:
            return "Network Device"
        elif len(open_ports) > 0:
            return "Network Device"
        else:
            return "Unknown"

    def _get_vendor_from_mac(self, mac: str) -> str:
        """Enhanced vendor lookup from MAC address OUI"""
        if not mac:
            return "Unknown"

        # Extract OUI (first 3 octets)
        oui = mac.replace(':', '').replace('-', '').upper()[:6]

        # Common OT/ICS vendor OUI database
        oui_database = {
            # Cisco
            '000142': 'Cisco', '00D0BC': 'Cisco', '001217': 'Cisco', '0090BF': 'Cisco',
            # Rockwell/Allen-Bradley
            '00008E': 'Rockwell Automation', '0030A3': 'Rockwell Automation',
            # Siemens
            '000E8C': 'Siemens', '00508B': 'Siemens', '7C2F80': 'Siemens',
            # Schneider Electric
            '0080F4': 'Schneider Electric', '00C0F2': 'Schneider Electric',
            # Honeywell
            '00A07E': 'Honeywell', '002582': 'Honeywell',
            # ABB
            '00306E': 'ABB', '00801F': 'ABB',
            # GE/Emerson
            '0050C2': 'GE', '00D0C9': 'Emerson',
            # HP/Aruba
            '001A4B': 'HP', '00266C': 'HP', '6C3BE5': 'Aruba',
            # Xerox
            '001048': 'Xerox', '080017': 'Xerox', '00093B': 'Xerox',
            # Cameras
            '001D7E': 'Hikvision', '547388': 'Hikvision', '446D6D': 'Dahua',
            # T-Mobile/Routers
            '8C1F94': 'T-Mobile', '001DD6': 'T-Mobile',
            # Common vendors
            '001B21': 'Intel', '00155D': 'Dell', '00502B': 'Raspberry Pi',
            '001EC9': 'TP-Link', '2CF05D': 'Apple',
        }

        return oui_database.get(oui, "Unknown")

    def _detect_services(self, ip: str, open_ports: List[int]) -> List[str]:
        """Enhanced service detection with industrial protocol identification"""
        services = []

        # Port to service mapping
        port_services = {
            # Industrial Protocols
            502: "Modbus TCP",
            44818: "EtherNet/IP",
            2222: "EtherNet/IP",
            20000: "DNP3",
            2404: "IEC 60870-5-104",
            47808: "BACnet",
            102: "S7comm",
            9600: "OMRON FINS",
            # Standard services
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            88: "Kerberos",
            110: "POP3",
            139: "NetBIOS",
            143: "IMAP",
            179: "BGP",
            389: "LDAP",
            443: "HTTPS",
            445: "SMB",
            631: "IPP",
            1433: "MSSQL",
            3306: "MySQL",
            3389: "RDP",
            5432: "PostgreSQL",
            5900: "VNC",
            8080: "HTTP-Alt",
            8443: "HTTPS-Alt",
            9100: "JetDirect",
        }

        for port in open_ports:
            if port in port_services:
                services.append(port_services[port])
            else:
                services.append(f"Port-{port}")

        return services


# ==========================================
# BACKWARD COMPATIBILITY
# ==========================================

# Legacy class name support
NetworkScanner = EnterpriseNetworkScanner


if __name__ == "__main__":
    # Test the scanner
    print("🧪 Testing EnterpriseNetworkScanner...")
    scanner = EnterpriseNetworkScanner(max_workers=20)

    test_subnets = ["192.168.1.0/24"]
    devices = scanner.scan_multiple_subnets(test_subnets)

    print(f"\n✅ Found {len(devices)} devices:")
    for device in devices:
        print(f"   • {device['ip_address']} - {device['hostname']} ({device['device_type']})")

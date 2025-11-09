import socket
import subprocess
import platform
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys

# Add src to path for ML imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class EnterpriseNetworkScanner:
    """Enterprise-grade OT/ICS Network Scanner with ML Integration"""

    def __init__(self, enable_ml=True):
        self.timeout = 1.0  # Reduced from 2.0 to 1.0 for faster scanning
        self.enable_ml = enable_ml
        self.ml_classifier = None
        self.ml_detector = None

        # Initialize ML components if enabled
        if self.enable_ml:
            self._initialize_ml()

        self.ot_ports = {
            502: 'Modbus',
            44818: 'EtherNet/IP',
            2222: 'EtherNet/IP',
            102: 'Siemens S7',
            20000: 'DNP3',
            4840: 'OPC UA',
            47808: 'BACnet',
            1911: 'Niagara Fox',
            789: 'RedLion Crimson',
            5094: 'ProfiNet',
            9100: 'Printer'
        }

    def _initialize_ml(self):
        """Initialize ML components for device analysis"""
        try:
            from ml.utils.device_feature_extractor import DeviceRiskClassifier
            from scanner.ml_integration import MLAnomalyDetector

            print("[ML] Initializing ML-powered device analysis...")
            self.ml_classifier = DeviceRiskClassifier()
            print("[ML] ✓ Device risk classifier loaded")

            # Optional: Load network anomaly detector
            try:
                self.ml_detector = MLAnomalyDetector()
                if self.ml_detector.is_loaded:
                    print("[ML] ✓ Network anomaly detector loaded")
                else:
                    self.ml_detector = None
                    print("[ML] ⚠ Network anomaly detector not available")
            except:
                self.ml_detector = None
                print("[ML] ⚠ Network anomaly detector not available")

            print("[ML] ML integration enabled\n")

        except Exception as e:
            print(f"[ML] ⚠ ML components not available: {e}")
            print("[ML] Continuing with basic scanning...\n")
            self.ml_classifier = None
            self.ml_detector = None
            self.enable_ml = False
        
    def scan_target(self, ip: str, verbose: bool = False) -> Dict:
        """Main scan method for a single target with ML integration

        Args:
            ip: Target IP address
            verbose: Enable verbose logging (default False for parallel scans)
        """
        if verbose:
            print(f"[*] Starting scan of {ip}...")

        result = {
            'ip': ip,
            'hostname': self._get_hostname(ip),
            'mac_address': 'Unknown',  # Will be populated after ping
            'vendor': 'Unknown',
            'status': 'unknown',
            'open_ports': [],
            'ot_protocols': [],
            'vulnerabilities': [],
            'services': []
        }

        # Check if host is alive FIRST (this populates ARP table)
        if not self._is_alive(ip):
            result['status'] = 'offline'
            # Still try to get MAC even for offline hosts (might be in ARP cache)
            result['mac_address'] = self._get_mac(ip)
            if result['mac_address'] != 'Unknown':
                result['vendor'] = self.get_vendor_from_mac(result['mac_address'])
            return result

        result['status'] = 'online'

        # Get MAC address (ARP table should be populated from ping above)
        result['mac_address'] = self._get_mac(ip)

        # Get vendor from MAC
        if result['mac_address'] != 'Unknown':
            result['vendor'] = self.get_vendor_from_mac(result['mac_address'])

        # Scan ports
        result['open_ports'] = self._scan_ports(ip)

        # Check for OT protocols
        result['ot_protocols'] = self._check_ot_protocols(ip, result['open_ports'])

        # Check for vulnerabilities
        result['vulnerabilities'] = self._check_vulnerabilities(result)

        # ML-powered analysis
        if self.enable_ml and self.ml_classifier:
            ml_analysis = self._perform_ml_analysis(result)
            result['ml_analysis'] = ml_analysis
        else:
            result['ml_analysis'] = None

        return result

    def _perform_ml_analysis(self, scan_result: Dict) -> Dict:
        """Perform ML-powered device analysis

        Args:
            scan_result: Device scan results

        Returns:
            Dictionary containing ML analysis results
        """
        ml_result = {
            'enabled': True,
            'risk_classification': None,
            'anomaly_detection': None,
            'device_profile': None
        }

        try:
            # 1. Device Risk Classification
            if self.ml_classifier:
                classification = self.ml_classifier.classify_device(scan_result)
                ml_result['risk_classification'] = classification

            # 2. Device Profile Analysis
            ml_result['device_profile'] = self._analyze_device_profile(scan_result)

            # 3. Anomaly flags based on unusual patterns
            ml_result['anomaly_flags'] = self._detect_anomalous_patterns(scan_result)

        except Exception as e:
            print(f"  [ML] ⚠ Error in ML analysis: {e}")
            ml_result['error'] = str(e)

        return ml_result

    def _analyze_device_profile(self, scan_result: Dict) -> Dict:
        """Analyze device profile and characteristics with enhanced OT/IT classification"""
        profile = {
            'device_type': 'Unknown',
            'is_ot_device': False,
            'confidence': 0.0,
            'characteristics': [],
            'category': 'Unknown'  # OT, IT, or Hybrid
        }

        open_ports = scan_result.get('open_ports', [])
        ot_protocols = scan_result.get('ot_protocols', [])
        vendor = scan_result.get('vendor', 'Unknown')

        # Check if vendor is a known OT/ICS vendor
        ot_vendors = [
            'Rockwell', 'Allen-Bradley', 'Siemens', 'Schneider', 'Modicon',
            'ABB', 'Honeywell', 'Emerson', 'Yokogawa', 'General Electric',
            'GE Fanuc', 'Phoenix Contact', 'Mitsubishi', 'Omron', 'WAGO',
            'Beckhoff'
        ]
        is_ot_vendor = any(ot_v in vendor for ot_v in ot_vendors)

        # Determine if it's an OT device based on multiple factors
        if ot_protocols:
            profile['is_ot_device'] = True
            profile['category'] = 'OT'
            profile['confidence'] = min(len(ot_protocols) * 0.25 + 0.5, 0.95)

            # Classify specific OT device type based on protocols
            protocol_names = [p.get('protocol', '') for p in ot_protocols]

            if 'Modbus' in protocol_names or 'Siemens S7' in protocol_names or 'EtherNet/IP' in protocol_names:
                profile['device_type'] = 'PLC (Programmable Logic Controller)'
                profile['characteristics'].append('Industrial Controller')
                profile['characteristics'].append('Critical OT Asset')
            elif 'OPC UA' in protocol_names:
                profile['device_type'] = 'SCADA Server/HMI'
                profile['characteristics'].append('Supervisory Control System')
                profile['characteristics'].append('High-Value Target')
            elif 'DNP3' in protocol_names:
                profile['device_type'] = 'RTU/SCADA Device'
                profile['characteristics'].append('Remote Terminal Unit')
                profile['characteristics'].append('Utility/Power System')
            elif 'BACnet' in protocol_names:
                profile['device_type'] = 'Building Management System (BMS)'
                profile['characteristics'].append('HVAC/Building Control')
            elif 'ProfiNet' in protocol_names:
                profile['device_type'] = 'Industrial Ethernet Device'
                profile['characteristics'].append('Factory Automation')
            else:
                profile['device_type'] = 'OT/ICS Device'
                profile['characteristics'].append('Industrial Protocol Detected')

            # Check for hybrid (OT device with IT services)
            services = [p.get('service', '').lower() for p in open_ports]
            if 'http' in str(services) or 'ssh' in services or 'smb' in str(services):
                profile['category'] = 'Hybrid (OT with IT Services)'
                profile['characteristics'].append('Has IT Management Interface')

        elif is_ot_vendor:
            # OT vendor but no OT protocols detected - likely OT support device
            profile['is_ot_device'] = True
            profile['category'] = 'OT Support'
            profile['device_type'] = 'OT Support Device/Engineering Workstation'
            profile['confidence'] = 0.6
            profile['characteristics'].append('OT Vendor Equipment')
            profile['characteristics'].append('Possible Engineering Station')

        else:
            # IT device classification based on services and ports
            profile['is_ot_device'] = False
            profile['category'] = 'IT'
            services = [p.get('service', '').lower() for p in open_ports]
            port_numbers = [p.get('port', 0) for p in open_ports]

            # Detailed IT device classification
            if 80 in port_numbers or 443 in port_numbers or 8080 in port_numbers:
                if 22 in port_numbers:  # SSH + Web
                    profile['device_type'] = 'Web/Application Server'
                    profile['confidence'] = 0.75
                else:
                    profile['device_type'] = 'Web Server/Workstation'
                    profile['confidence'] = 0.65
                profile['characteristics'].append('Web Services')

            elif 22 in port_numbers:  # SSH
                if 445 in port_numbers:  # SSH + SMB
                    profile['device_type'] = 'Linux File Server'
                    profile['confidence'] = 0.8
                else:
                    profile['device_type'] = 'Server/Network Device'
                    profile['confidence'] = 0.7
                profile['characteristics'].append('SSH Remote Access')

            elif 445 in port_numbers or 139 in port_numbers:  # SMB
                profile['device_type'] = 'Windows File Server/Workstation'
                profile['confidence'] = 0.75
                profile['characteristics'].append('Windows File Sharing')

            elif 3389 in port_numbers:  # RDP
                profile['device_type'] = 'Windows Server/Workstation'
                profile['confidence'] = 0.8
                profile['characteristics'].append('Remote Desktop Enabled')

            elif 23 in port_numbers:  # Telnet
                profile['device_type'] = 'Network Device/Legacy System'
                profile['confidence'] = 0.6
                profile['characteristics'].append('Legacy Management')

            else:
                # Check for network infrastructure
                if len(port_numbers) < 5:
                    profile['device_type'] = 'Network Infrastructure'
                    profile['confidence'] = 0.5
                else:
                    profile['device_type'] = 'Generic IT Device'
                    profile['confidence'] = 0.4

        # Additional characteristics based on security posture
        if len(open_ports) > 15:
            profile['characteristics'].append('Excessive Open Ports')
        if len(open_ports) > 10:
            profile['characteristics'].append('Multiple Services Running')

        if scan_result.get('vulnerabilities'):
            vuln_count = len(scan_result['vulnerabilities'])
            if vuln_count > 0:
                profile['characteristics'].append(f'{vuln_count} Vulnerabilities Detected')

        # Add vendor info to characteristics if known
        if vendor != 'Unknown':
            profile['characteristics'].append(f'Vendor: {vendor}')

        return profile

    def _detect_anomalous_patterns(self, scan_result: Dict) -> List[Dict]:
        """Detect anomalous patterns in device configuration"""
        anomalies = []

        open_ports = scan_result.get('open_ports', [])
        ot_protocols = scan_result.get('ot_protocols', [])

        # Anomaly 1: OT protocol with Telnet/FTP (security issue)
        if ot_protocols:
            insecure_services = [p for p in open_ports
                               if p.get('service') in ['Telnet', 'FTP']]
            if insecure_services:
                anomalies.append({
                    'type': 'security_anomaly',
                    'severity': 'high',
                    'description': 'OT device with insecure remote access protocols',
                    'details': f"Found {len(insecure_services)} insecure service(s) on OT device"
                })

        # Anomaly 2: Excessive open ports
        if len(open_ports) > 15:
            anomalies.append({
                'type': 'configuration_anomaly',
                'severity': 'medium',
                'description': 'Unusually high number of open ports',
                'details': f"{len(open_ports)} ports open - potential over-exposure"
            })

        # Anomaly 3: Multiple critical OT protocols on same device
        critical_protocols = [p for p in ot_protocols
                            if p.get('risk', '') == 'HIGH']
        if len(critical_protocols) > 2:
            anomalies.append({
                'type': 'deployment_anomaly',
                'severity': 'medium',
                'description': 'Multiple critical OT protocols on single device',
                'details': 'May indicate improper network segmentation'
            })

        # Anomaly 4: No SSH but has other services (on IT devices)
        if not ot_protocols and len(open_ports) > 3:
            has_ssh = any(p.get('service') == 'SSH' for p in open_ports)
            if not has_ssh:
                anomalies.append({
                    'type': 'security_anomaly',
                    'severity': 'low',
                    'description': 'Device lacks secure remote access',
                    'details': 'SSH not detected despite multiple services'
                })

        return anomalies
    
    def _is_alive(self, ip: str) -> bool:
        """Check if host is alive"""
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', '-w', '500', ip]  # Reduced from 1000ms to 500ms

        try:
            output = subprocess.run(command, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL, timeout=1)  # Reduced from 2s to 1s
            return output.returncode == 0
        except:
            return False
    
    def _get_hostname(self, ip: str) -> str:
        """Get hostname from IP"""
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return ip
    
    def _get_mac(self, ip: str) -> str:
        """Get MAC address from ARP table with improved detection

        Note: This should be called AFTER ping/connectivity check to ensure
        ARP table is populated. However, it includes a fallback ping if needed.
        """
        import time
        import re

        # Try method 1: Standard ARP command (works on Windows and Linux)
        mac_address = None
        try:
            if platform.system().lower() == 'windows':
                # Windows: arp -a
                output = subprocess.check_output(['arp', '-a'],
                                               universal_newlines=True,
                                               timeout=1)  # Reduced from 2s to 1s
            else:
                # Linux/Unix: arp -n (numeric, faster)
                output = subprocess.check_output(['arp', '-n'],
                                               universal_newlines=True,
                                               timeout=1)  # Reduced from 2s to 1s

            # Parse ARP output
            for line in output.split('\n'):
                if ip in line:
                    # Look for MAC address pattern (XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX)
                    mac_pattern = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
                    match = re.search(mac_pattern, line)
                    if match:
                        mac_address = match.group(0)
                        # Normalize to colon format and return
                        return mac_address.replace('-', ':').upper()
        except Exception as e:
            pass

        # Try method 2: ip neigh (Linux alternative)
        if platform.system().lower() != 'windows':
            try:
                output = subprocess.check_output(['ip', 'neigh', 'show', ip],
                                               universal_newlines=True,
                                               timeout=1)  # Reduced from 2s to 1s
                mac_pattern = r'([0-9A-Fa-f]{2}:){5}([0-9A-Fa-f]{2})'
                match = re.search(mac_pattern, output)
                if match:
                    return match.group(0).upper()
            except:
                pass

        # Try method 3: arp -a <specific_ip> (targeted query)
        try:
            output = subprocess.check_output(['arp', '-a', ip],
                                           universal_newlines=True,
                                           timeout=1)  # Reduced from 2s to 1s
            mac_pattern = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
            match = re.search(mac_pattern, output)
            if match:
                mac_address = match.group(0)
                return mac_address.replace('-', ':').upper()
        except:
            pass

        # Fallback: If ARP table doesn't have the entry, try pinging and retry
        # This handles cases where scan_target is called without prior ping
        if mac_address is None:
            try:
                param = '-n' if platform.system().lower() == 'windows' else '-c'
                subprocess.run(['ping', param, '1', '-w', '500', ip],  # Reduced from 1000ms to 500ms
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             timeout=1)  # Reduced from 2s to 1s
                # Small delay to ensure ARP table is updated
                time.sleep(0.2)  # Reduced from 0.3s to 0.2s

                # Retry ARP lookup after ping
                if platform.system().lower() == 'windows':
                    output = subprocess.check_output(['arp', '-a'],
                                                   universal_newlines=True,
                                                   timeout=1)  # Reduced from 2s to 1s
                else:
                    output = subprocess.check_output(['arp', '-n'],
                                                   universal_newlines=True,
                                                   timeout=1)  # Reduced from 2s to 1s

                for line in output.split('\n'):
                    if ip in line:
                        mac_pattern = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
                        match = re.search(mac_pattern, line)
                        if match:
                            mac_address = match.group(0)
                            return mac_address.replace('-', ':').upper()
            except:
                pass

        return "Unknown"
    
    def _scan_ports(self, ip: str, port_list: List[int] = None) -> List[Dict]:
        """Scan common ports on target"""
        if port_list is None:
            # Common ports + OT ports
            port_list = [21, 22, 23, 80, 443, 445, 502, 102, 44818, 
                        2222, 20000, 4840, 47808, 1911, 789, 5094,
                        8080, 8443, 3389, 5900]
        
        open_ports = []
        
        def check_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                result = sock.connect_ex((ip, port))
                sock.close()
                
                if result == 0:
                    service = self._identify_service(port)
                    return {
                        'port': port,
                        'service': service,
                        'protocol': 'tcp',
                        'state': 'open'
                    }
            except:
                pass
            return None
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = executor.map(check_port, port_list)
            open_ports = [r for r in results if r is not None]
        
        return sorted(open_ports, key=lambda x: x['port'])
    
    def _identify_service(self, port: int) -> str:
        """Identify service by port number"""
        common_services = {
            21: 'FTP',
            22: 'SSH',
            23: 'Telnet',
            80: 'HTTP',
            443: 'HTTPS',
            445: 'SMB',
            3389: 'RDP',
            5900: 'VNC',
            8080: 'HTTP-Alt',
            8443: 'HTTPS-Alt'
        }
        
        if port in self.ot_ports:
            return self.ot_ports[port]
        
        return common_services.get(port, f'unknown-{port}')
    
    def _check_ot_protocols(self, ip: str, open_ports: List[Dict]) -> List[Dict]:
        """Check for OT/ICS protocols"""
        ot_found = []
        
        for port_info in open_ports:
            port = port_info['port']
            
            if port in self.ot_ports:
                protocol_name = self.ot_ports[port]
                
                ot_found.append({
                    'protocol': protocol_name,
                    'port': port,
                    'details': f'{protocol_name} service detected on port {port}',
                    'risk': 'HIGH' if port in [502, 102, 44818] else 'MEDIUM'
                })
        
        return ot_found
    
    def _check_vulnerabilities(self, result: Dict) -> List[Dict]:
        """Check for common vulnerabilities"""
        vulns = []
        
        # Check for insecure protocols
        for port_info in result['open_ports']:
            port = port_info['port']
            service = port_info['service']
            
            # Telnet vulnerability
            if port == 23:
                vulns.append({
                    'severity': 'high',
                    'description': 'Telnet service detected - unencrypted protocol',
                    'recommendation': 'Disable Telnet and use SSH instead',
                    'cve': 'N/A'
                })
            
            # FTP vulnerability
            if port == 21:
                vulns.append({
                    'severity': 'medium',
                    'description': 'FTP service detected - unencrypted file transfer',
                    'recommendation': 'Use SFTP or FTPS instead',
                    'cve': 'N/A'
                })
            
            # Exposed OT protocols
            if port in self.ot_ports:
                vulns.append({
                    'severity': 'critical',
                    'description': f'{self.ot_ports[port]} exposed without authentication',
                    'recommendation': 'Implement firewall rules and authentication',
                    'cve': 'ICS-ALERT-EXPOSURE'
                })
        
        # Check for SMB
        if any(p['port'] == 445 for p in result['open_ports']):
            vulns.append({
                'severity': 'high',
                'description': 'SMB service exposed - potential for EternalBlue',
                'recommendation': 'Apply MS17-010 patch and restrict SMB access',
                'cve': 'CVE-2017-0144'
            })
        
        return vulns
    
    def get_vendor_from_mac(self, mac: str) -> str:
        """Get vendor from MAC address with comprehensive OUI database"""
        if not mac or mac == "Unknown" or mac == ":::":
            return "Unknown"

        # Comprehensive OUI database (first 3 octets) - Major OT/ICS and IT vendors
        oui_db = {
            # Major OT/ICS Vendors
            "00:1D:9C": "Rockwell Automation",
            "00:00:BC": "Allen-Bradley (Rockwell)",
            "00:C0:A8": "Rockwell Automation",
            "88:90:8D": "Siemens",
            "A0:36:BC": "Siemens",
            "00:0E:8C": "Siemens",
            "00:1B:1B": "Siemens",
            "00:50:7F": "Schneider Electric",
            "00:80:F4": "Schneider Electric (Modicon)",
            "00:06:29": "Schneider Electric",
            "00:C0:F2": "Schneider Electric",
            "00:80:7C": "ABB",
            "00:18:FE": "ABB",
            "BC:AE:C5": "ABB",
            "00:10:A4": "Honeywell",
            "00:E0:4C": "Honeywell",
            "00:50:C2": "Emerson Process Management",
            "00:1E:8F": "Emerson",
            "00:D0:C9": "Emerson",
            "00:0E:64": "Yokogawa",
            "00:80:63": "Yokogawa",
            "00:00:5E": "General Electric",
            "00:30:6E": "GE Fanuc Automation",
            "00:A0:45": "Phoenix Contact",
            "00:0E:B0": "Phoenix Contact",
            "00:50:A0": "Mitsubishi Electric",
            "00:80:63": "Mitsubishi Electric",
            "00:19:99": "Omron",
            "00:00:6B": "WAGO",
            "00:30:DE": "Beckhoff Automation",
            "00:01:05": "Beckhoff",

            # Network Equipment Vendors
            "00:1C:7F": "Check Point Software",
            "A4:53:0E": "Cisco",
            "00:1D:A2": "Cisco",
            "00:0D:EC": "Cisco",
            "00:E0:1E": "Cisco",
            "00:26:0B": "Cisco",
            "D0:D0:FD": "Cisco",
            "00:50:56": "VMware",
            "00:0C:29": "VMware",
            "00:1C:14": "VMware",
            "00:24:1D": "Fortinet",
            "00:09:0F": "Fortinet",
            "70:4C:A5": "Fortinet",
            "00:03:FF": "Microsoft",
            "00:50:F2": "Microsoft",
            "00:12:5A": "Microsoft",
            "08:00:27": "Oracle VirtualBox",
            "00:04:23": "Intel",
            "00:1B:21": "Intel",
            "00:13:20": "Intel",
            "AC:DE:48": "Intel",
            "00:0A:95": "Dell",
            "00:14:22": "Dell",
            "B8:2A:72": "Dell",
            "D0:67:E5": "Dell",
            "00:1E:68": "Hewlett Packard (HP)",
            "00:23:7D": "Hewlett Packard",
            "00:24:81": "Hewlett Packard",
            "EC:B1:D7": "Hewlett Packard",
            "F8:A2:D6": "Xerox",
            "00:00:AA": "Xerox",
            "B0:99:D7": "Samsung",
            "00:12:FB": "Samsung",
            "00:1D:25": "Samsung",
            "00:18:0A": "Lenovo",
            "00:21:86": "Lenovo",
            "00:1C:25": "Lenovo",

            # Additional Generic
            "44:6D:7F": "Generic Device",
            "52:54:00": "QEMU Virtual NIC",
            "00:15:5D": "Microsoft Hyper-V",
            "00:05:69": "VMware ESX",
        }

        # Normalize MAC format and extract OUI
        try:
            mac_clean = mac.replace('-', ':').upper()
            oui = ':'.join(mac_clean.split(':')[:3])
            return oui_db.get(oui, "Unknown")
        except:
            return "Unknown"




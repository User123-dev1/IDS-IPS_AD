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
        self.timeout = 2.0
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
        
    def scan_target(self, ip: str) -> Dict:
        """Main scan method for a single target with ML integration"""
        print(f"[*] Starting scan of {ip}...")

        result = {
            'ip': ip,
            'hostname': self._get_hostname(ip),
            'mac_address': self._get_mac(ip),
            'vendor': 'Unknown',
            'status': 'unknown',
            'open_ports': [],
            'ot_protocols': [],
            'vulnerabilities': [],
            'services': []
        }

        # Get vendor from MAC
        if result['mac_address'] != 'Unknown':
            result['vendor'] = self.get_vendor_from_mac(result['mac_address'])

        # Check if host is alive
        if not self._is_alive(ip):
            result['status'] = 'offline'
            return result

        result['status'] = 'online'

        # Scan ports
        print(f"  [*] Scanning ports...")
        result['open_ports'] = self._scan_ports(ip)

        # Check for OT protocols
        print(f"  [*] Checking OT/ICS protocols...")
        result['ot_protocols'] = self._check_ot_protocols(ip, result['open_ports'])

        # Check for vulnerabilities
        print(f"  [*] Checking vulnerabilities...")
        result['vulnerabilities'] = self._check_vulnerabilities(result)

        # ML-powered analysis
        if self.enable_ml and self.ml_classifier:
            print(f"  [*] Running ML analysis...")
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

                # Add summary
                print(f"  [ML] Risk Level: {classification['risk_level'].upper()} " +
                      f"(Score: {classification['risk_score']:.2f})")

            # 2. Device Profile Analysis
            ml_result['device_profile'] = self._analyze_device_profile(scan_result)

            # 3. Anomaly flags based on unusual patterns
            ml_result['anomaly_flags'] = self._detect_anomalous_patterns(scan_result)

        except Exception as e:
            print(f"  [ML] ⚠ Error in ML analysis: {e}")
            ml_result['error'] = str(e)

        return ml_result

    def _analyze_device_profile(self, scan_result: Dict) -> Dict:
        """Analyze device profile and characteristics"""
        profile = {
            'device_type': 'Unknown',
            'is_ot_device': False,
            'confidence': 0.0,
            'characteristics': []
        }

        open_ports = scan_result.get('open_ports', [])
        ot_protocols = scan_result.get('ot_protocols', [])

        # Determine if it's an OT device
        if ot_protocols:
            profile['is_ot_device'] = True
            profile['confidence'] = min(len(ot_protocols) * 0.3 + 0.4, 1.0)

            # Classify device type based on protocols
            protocol_names = [p.get('protocol', '') for p in ot_protocols]

            if 'Modbus' in protocol_names or 'Siemens S7' in protocol_names:
                profile['device_type'] = 'PLC/Controller'
                profile['characteristics'].append('Industrial Controller')
            elif 'OPC UA' in protocol_names:
                profile['device_type'] = 'SCADA/HMI'
                profile['characteristics'].append('Supervisory System')
            elif 'BACnet' in protocol_names:
                profile['device_type'] = 'Building Automation'
                profile['characteristics'].append('BMS Device')
            else:
                profile['device_type'] = 'OT Device'

        else:
            # IT device classification
            services = [p.get('service', '').lower() for p in open_ports]

            if 'http' in str(services) or 'https' in str(services):
                profile['device_type'] = 'Web Server/Workstation'
                profile['characteristics'].append('Network Service')
            elif 'ssh' in services:
                profile['device_type'] = 'Server/Network Device'
                profile['characteristics'].append('Remote Access Enabled')
            elif 'smb' in str(services):
                profile['device_type'] = 'File Server/Workstation'
                profile['characteristics'].append('File Sharing')
            else:
                profile['device_type'] = 'Network Device'

            profile['confidence'] = 0.5

        # Add characteristics based on scan results
        if len(open_ports) > 10:
            profile['characteristics'].append('Multiple Services')
        if scan_result.get('vulnerabilities'):
            profile['characteristics'].append('Security Issues Detected')

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
        command = ['ping', param, '1', '-w', '1000', ip]
        
        try:
            output = subprocess.run(command, stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL, timeout=2)
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
        """Get MAC address from ARP table"""
        try:
            output = subprocess.check_output(['arp', '-a', ip], 
                                           universal_newlines=True, timeout=2)
            for line in output.split('\n'):
                if ip in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if ip in part and i + 1 < len(parts):
                            mac = parts[i + 1]
                            if '-' in mac or ':' in mac:
                                return mac.replace('-', ':')
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
        """Get vendor from MAC address"""
        if not mac or mac == "Unknown" or mac == ":::":
            return "Unknown"
        
        # OUI database (first 3 octets)
        oui_db = {
            "00:1C:7F": "Check Point Software",
            "00:1D:9C": "Rockwell Automation",
            "88:90:8D": "Siemens",
            "F8:A2:D6": "Xerox",
            "B0:99:D7": "Samsung",
            "A4:53:0E": "Cisco",
            "44:6D:7F": "Unknown Device"
        }

        oui = ':'.join(mac.split(':')[:3]).upper()
        return oui_db.get(oui, "Unknown")




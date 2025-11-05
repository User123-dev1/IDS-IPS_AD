"""
Asset Management and Data Processing Layer
Handles data processing, analytics, and business logic
"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import json

# Import our C++ scanner module
try:
    import scanner_module
except ImportError:
    print("Warning: C++ scanner module not available. Using mock data.")
    scanner_module = None


@dataclass
class Asset:
    id: int
    ip_address: str
    mac_address: str
    hostname: str
    device_type: str
    manufacturer: str
    model: str
    firmware_version: str
    protocol: str
    open_ports: List[int]
    is_ot_device: bool
    confidence: float
    status: str  # online, offline, warning, critical
    last_seen: datetime
    discovery_time: datetime
    risk_score: int
    vulnerabilities: List[str]
    compliance_status: Dict[str, str]
    location: str
    network_segment: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert asset to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data['last_seen'] = self.last_seen.isoformat()
        data['discovery_time'] = self.discovery_time.isoformat()
        return data

    @classmethod
    def from_scan_result(cls, scan_result, asset_id: int = None) -> 'Asset':
        """Create Asset from C++ scan result"""
        return cls(
            id=asset_id or 0,
            ip_address=scan_result.ip_address,
            mac_address=scan_result.mac_address,
            hostname=scan_result.hostname,
            device_type=scan_result.device_type,
            manufacturer=scan_result.manufacturer,
            model="",
            firmware_version="",
            protocol=scan_result.protocol,
            open_ports=scan_result.open_ports,
            is_ot_device=scan_result.is_ot_device,
            confidence=scan_result.confidence,
            status="online",
            last_seen=datetime.now(),
            discovery_time=datetime.now(),
            risk_score=0,
            vulnerabilities=[],
            compliance_status={},
            location="",
            network_segment=""
        )


class AssetDatabase:
    """Encrypted SQLite database for asset storage"""

    def __init__(self, db_path: str = "data/assets.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL UNIQUE,
                    mac_address TEXT,
                    hostname TEXT,
                    device_type TEXT,
                    manufacturer TEXT,
                    model TEXT,
                    firmware_version TEXT,
                    protocol TEXT,
                    open_ports TEXT,
                    is_ot_device BOOLEAN,
                    confidence REAL,
                    status TEXT,
                    last_seen TIMESTAMP,
                    discovery_time TIMESTAMP,
                    risk_score INTEGER,
                    vulnerabilities TEXT,
                    compliance_status TEXT,
                    location TEXT,
                    network_segment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_type TEXT,
                    target_range TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    assets_discovered INTEGER,
                    assets_updated INTEGER,
                    status TEXT,
                    results TEXT
                )
            ''')

            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_ip_address ON assets(ip_address)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_device_type ON assets(device_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_last_seen ON assets(last_seen)')

    def save_asset(self, asset: Asset) -> int:
        """Save or update asset in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO assets (
                    id, ip_address, mac_address, hostname, device_type,
                    manufacturer, model, firmware_version, protocol,
                    open_ports, is_ot_device, confidence, status,
                    last_seen, discovery_time, risk_score, vulnerabilities,
                    compliance_status, location, network_segment, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                asset.id if asset.id else None,
                asset.ip_address,
                asset.mac_address,
                asset.hostname,
                asset.device_type,
                asset.manufacturer,
                asset.model,
                asset.firmware_version,
                asset.protocol,
                json.dumps(asset.open_ports),
                asset.is_ot_device,
                asset.confidence,
                asset.status,
                asset.last_seen,
                asset.discovery_time,
                asset.risk_score,
                json.dumps(asset.vulnerabilities),
                json.dumps(asset.compliance_status),
                asset.location,
                asset.network_segment,
                datetime.now()
            ))

            if asset.id is None:
                return conn.lastrowid
            return asset.id

    def get_all_assets(self) -> List[Asset]:
        """Retrieve all assets from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM assets ORDER BY discovery_time DESC')

            assets = []
            for row in cursor.fetchall():
                asset = Asset(
                    id=row['id'],
                    ip_address=row['ip_address'],
                    mac_address=row['mac_address'] or '',
                    hostname=row['hostname'] or '',
                    device_type=row['device_type'] or '',
                    manufacturer=row['manufacturer'] or '',
                    model=row['model'] or '',
                    firmware_version=row['firmware_version'] or '',
                    protocol=row['protocol'] or '',
                    open_ports=json.loads(row['open_ports'] or '[]'),
                    is_ot_device=bool(row['is_ot_device']),
                    confidence=row['confidence'] or 0.0,
                    status=row['status'] or 'unknown',
                    last_seen=datetime.fromisoformat(row['last_seen']) if row['last_seen'] else datetime.now(),
                    discovery_time=datetime.fromisoformat(row['discovery_time']) if row[
                        'discovery_time'] else datetime.now(),
                    risk_score=row['risk_score'] or 0,
                    vulnerabilities=json.loads(row['vulnerabilities'] or '[]'),
                    compliance_status=json.loads(row['compliance_status'] or '{}'),
                    location=row['location'] or '',
                    network_segment=row['network_segment'] or ''
                )
                assets.append(asset)

            return assets

    def get_asset_statistics(self) -> Dict[str, Any]:
        """Generate asset statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Total assets
            total = conn.execute('SELECT COUNT(*) FROM assets').fetchone()[0]

            # Online/Offline counts
            online = conn.execute("SELECT COUNT(*) FROM assets WHERE status = 'online'").fetchone()[0]
            offline = total - online

            # OT device count
            ot_devices = conn.execute('SELECT COUNT(*) FROM assets WHERE is_ot_device = 1').fetchone()[0]

            # Device types
            device_types = conn.execute('''
                SELECT device_type, COUNT(*) as count 
                FROM assets 
                WHERE device_type IS NOT NULL AND device_type != ''
                GROUP BY device_type
            ''').fetchall()

            # Protocols
            protocols = conn.execute('''
                SELECT protocol, COUNT(*) as count 
                FROM assets 
                WHERE protocol IS NOT NULL AND protocol != ''
                GROUP BY protocol
            ''').fetchall()

            return {
                'total_assets': total,
                'online_assets': online,
                'offline_assets': offline,
                'ot_devices': ot_devices,
                'it_devices': total - ot_devices,
                'device_types': {row[0]: row[1] for row in device_types},
                'protocols': {row[0]: row[1] for row in protocols},
                'last_updated': datetime.now().isoformat()
            }


class AssetManager:
    """Main asset management class"""

    def __init__(self, db_path: str = "data/assets.db"):
        self.db = AssetDatabase(db_path)
        self.logger = logging.getLogger(__name__)
        self.scanner = scanner_module.NetworkScanner() if scanner_module else None

        # Set up callbacks
        if self.scanner:
            self.scanner.set_progress_callback(self._on_scan_progress)
            self.scanner.set_result_callback(self._on_scan_result)

    def _on_scan_progress(self, percentage: int, status: str):
        """Callback for scan progress"""
        self.logger.info(f"Scan progress: {percentage}% - {status}")

    def _on_scan_result(self, scan_result):
        """Callback for scan result"""
        asset = Asset.from_scan_result(scan_result)
        self.db.save_asset(asset)
        self.logger.info(f"Discovered asset: {asset.ip_address} ({asset.device_type})")

    def start_network_scan(self, target_range: str, **kwargs) -> List[Asset]:
        """Start network scan using C++ scanner"""
        if not self.scanner:
            self.logger.error("C++ scanner not available")
            return []

        self.logger.info(f"Starting network scan: {target_range}")

        # Configure scan
        config = scanner_module.ScanConfig()
        config.target_range = target_range
        config.timeout_ms = kwargs.get('timeout_ms', 5000)
        config.max_threads = kwargs.get('max_threads', 50)
        config.protocol_detection = kwargs.get('protocol_detection', True)
        config.deep_scan = kwargs.get('deep_scan', False)

        try:
            # Perform scan
            scan_results = self.scanner.scan_network(config)

            # Convert results to Asset objects and save
            assets = []
            for result in scan_results:
                asset = Asset.from_scan_result(result)
                asset.id = self.db.save_asset(asset)
                assets.append(asset)

            self.logger.info(f"Scan completed. Discovered {len(assets)} assets.")
            return assets

        except Exception as e:
            self.logger.error(f"Scan failed: {str(e)}")
            return []

    def get_assets(self) -> List[Asset]:
        """Get all assets"""
        return self.db.get_all_assets()

    def get_statistics(self) -> Dict[str, Any]:
        """Get asset statistics"""
        return self.db.get_asset_statistics()

    def analyze_network_topology(self) -> Dict[str, Any]:
        """Analyze network topology from discovered assets"""
        assets = self.get_assets()

        # Group by network segments
        segments = {}
        for asset in assets:
            # Extract network segment from IP
            ip_parts = asset.ip_address.split('.')
            if len(ip_parts) >= 3:
                segment = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
                if segment not in segments:
                    segments[segment] = []
                segments[segment].append(asset)

        # Analyze protocols per segment
        topology = {}
        for segment, segment_assets in segments.items():
            protocols = {}
            device_types = {}

            for asset in segment_assets:
                if asset.protocol:
                    protocols[asset.protocol] = protocols.get(asset.protocol, 0) + 1
                if asset.device_type:
                    device_types[asset.device_type] = device_types.get(asset.device_type, 0) + 1

            topology[segment] = {
                'asset_count': len(segment_assets),
                'ot_devices': sum(1 for a in segment_assets if a.is_ot_device),
                'protocols': protocols,
                'device_types': device_types,
                'assets': [a.to_dict() for a in segment_assets]
            }

        return topology

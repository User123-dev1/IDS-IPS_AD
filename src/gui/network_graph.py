#!/usr/bin/env python3
"""
Enhanced Network Graph (Cleaned & Fixed)
- Removed duplicate methods (get_display_name, _setup_visual, _classify_device_type)
- Use a single, richer device classifier (vendor + hostname)
- Unified visuals (gradient fill, vendor dot, labels, type badge, status dot)
- Avoid duplicate edges; keep edges in sync while dragging
- Minor fixes in topology discovery and UI wiring
"""

import math
import sys
from typing import Dict, List, Set, Optional

from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsEllipseItem,
    QGraphicsTextItem, QGraphicsLineItem, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QGroupBox, QApplication, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QRadialGradient


class NetworkNode(QGraphicsEllipseItem):
    """Enhanced network node with enterprise vendor support"""

    NODE_TYPES = {
        # Routers
        'router': {'color': QColor(255, 193, 7), 'size': 50},
        'cisco_router': {'color': QColor(0, 122, 204), 'size': 50},
        'checkpoint_router': {'color': QColor(230, 70, 30), 'size': 50},

        # Firewalls
        'firewall': {'color': QColor(244, 67, 54), 'size': 50},
        'checkpoint_firewall': {'color': QColor(200, 30, 30), 'size': 50},
        'cisco_firewall': {'color': QColor(150, 50, 150), 'size': 50},

        # Switches
        'switch': {'color': QColor(255, 152, 0), 'size': 45},
        'cisco_switch': {'color': QColor(0, 100, 180), 'size': 45},

        # Servers
        'server': {'color': QColor(103, 58, 183), 'size': 40},

        # VMware
        'vmware_esxi': {'color': QColor(0, 188, 212), 'size': 45},
        'vmware_vcenter': {'color': QColor(0, 150, 200), 'size': 45},
        'vmware_vm': {'color': QColor(100, 200, 255), 'size': 35},

        # Industrial/PLC
        'rockwell_plc': {'color': QColor(200, 100, 0), 'size': 40},
        'device': {'color': QColor(76, 175, 80), 'size': 35},

        # Wireless
        'wireless_ap': {'color': QColor(150, 100, 200), 'size': 35},

        # Unknown
        'unknown': {'color': QColor(96, 125, 139), 'size': 30}
    }

    def __init__(self, device_data: dict):
        super().__init__()
        self.device_data = device_data
        self.edges: Set["NetworkEdge"] = set()

        # Determine device type using unified classifier
        self.device_type = self._classify_device_type()
        self.props = self.NODE_TYPES.get(self.device_type, self.NODE_TYPES['unknown'])

        # Visuals & behavior
        self._setup_visual()
        self._setup_behavior()

        print(f"🎨 Created node: {self.get_display_name()} at (0,0) [{self.device_type}]")

    # -------- Behavior & interactions --------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.screenPos().toPoint())
        else:
            print(f"🎯 Selected: {self.get_display_name()}")
            super().mousePressEvent(event)

    def hoverEnterEvent(self, event):
        self.setScale(1.2)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setScale(1.0)
        super().hoverLeaveEvent(event)

    def _show_context_menu(self, global_pos):
        menu = QMenu()
        ip = self.device_data.get('ip_address', 'Unknown')
        hostname = self.device_data.get('hostname', 'Unknown')

        hdr = menu.addAction(f"📋 {hostname}")
        hdr.setEnabled(False)
        ip_action = menu.addAction(f"🌐 {ip}")
        ip_action.setEnabled(False)
        menu.addSeparator()

        ping_action = menu.addAction("🔍 Ping Device")
        ping_action.triggered.connect(self._ping_device)
        scan_action = menu.addAction("🔎 Port Scan")
        scan_action.triggered.connect(self._port_scan)
        traceroute_action = menu.addAction("🛤️ Traceroute")
        traceroute_action.triggered.connect(self._traceroute)
        menu.addSeparator()

        pulse_action = menu.addAction("💫 Pulse Animation")
        pulse_action.triggered.connect(self._start_pulse)
        highlight_action = menu.addAction("✨ Highlight Connections")
        highlight_action.triggered.connect(self._highlight_connections)
        menu.addSeparator()

        details_action = menu.addAction("ℹ️ Device Details")
        details_action.triggered.connect(self._show_details)

        menu.exec(global_pos)

    # ---- Fake actions / stubs ----

    def _ping_device(self):
        ip = self.device_data.get('ip_address', 'Unknown')
        print(f"🔍 Pinging {ip}...")
        self._show_action_message("Ping", f"Pinging {ip}...")

    def _port_scan(self):
        ip = self.device_data.get('ip_address', 'Unknown')
        print(f"🔎 Port scanning {ip}...")
        self._show_action_message("Port Scan", f"Scanning ports on {ip}...")

    def _traceroute(self):
        ip = self.device_data.get('ip_address', 'Unknown')
        print(f"🛤️ Traceroute to {ip}...")
        self._show_action_message("Traceroute", f"Tracing route to {ip}...")

    # ---- Visual helpers ----

    def _start_pulse(self):
        print(f"💫 Starting pulse animation for {self.get_display_name()}")
        if not hasattr(self, 'pulse_timer'):
            self.pulse_timer = QTimer()
            self.pulse_timer.timeout.connect(self._pulse_step)
        self.pulse_count = 0
        self.pulse_timer.start(100)

    def _pulse_step(self):
        if self.pulse_count < 10:
            self.setScale(1.4 if self.pulse_count % 2 == 0 else 1.0)
            self.pulse_count += 1
        else:
            self.pulse_timer.stop()
            self.setScale(1.0)

    def _highlight_connections(self):
        print(f"✨ Highlighting connections for {self.get_display_name()}")
        for edge in self.edges:
            pen = edge.pen()
            pen.setWidthF(4.0)
            edge.setPen(pen)
            QTimer.singleShot(1500, lambda e=edge: e.reset_pen())
        self._show_action_message("Highlight", "Highlighting network connections...")

    def _show_details(self):
        details = [
            f"Hostname: {self.device_data.get('hostname', 'Unknown')}",
            f"IP Address: {self.device_data.get('ip_address', 'Unknown')}",
            f"Device Type: {self.device_type}",
            f"Status: {self.device_data.get('status', 'Unknown')}",
        ]
        if 'mac_address' in self.device_data:
            details.append(f"MAC Address: {self.device_data['mac_address']}")
        if 'vendor' in self.device_data:
            details.append(f"Vendor: {self.device_data['vendor']}")
        if self.device_data.get('services'):
            details.append(f"Services: {', '.join(self.device_data['services'])}")

        msg = QMessageBox()
        msg.setWindowTitle("Device Details")
        msg.setText(f"📋 {self.get_display_name()} Details")
        msg.setDetailedText('\n'.join(details))
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def _show_action_message(self, action: str, message: str):
        print(f"🔧 {action}: {message}")
        temp_label = QGraphicsTextItem(f"{action}...", self)
        temp_label.setDefaultTextColor(QColor(255, 255, 0))
        temp_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        temp_label.setPos(-30, -60)
        QTimer.singleShot(2000, lambda l=temp_label: self._remove_temp_label(l))

    def _remove_temp_label(self, label: QGraphicsTextItem):
        try:
            if label.scene():
                label.scene().removeItem(label)
        except Exception:
            pass

    # -------- Setup helpers (unified) --------

    def _setup_visual(self):
        size = self.props['size']
        color: QColor = self.props['color']

        self.setRect(-size / 2, -size / 2, size, size)

        gradient = QRadialGradient(0, 0, size / 2)
        gradient.setColorAt(0, color.lighter(150))
        gradient.setColorAt(0.8, color)
        gradient.setColorAt(1, color.darker(120))
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(color.darker(150), 3))

        # Vendor indicator (small dot above the circle)
        vendor = (self.device_data.get('vendor') or '').lower()
        vendor_colors = {
            'cisco': QColor(0, 122, 204),
            'checkpoint': QColor(230, 70, 30),
            'vmware': QColor(0, 188, 212),
            'rockwell': QColor(200, 100, 0),
            'microsoft': QColor(0, 120, 215),
        }
        v_col = vendor_colors.get(vendor, QColor(128, 128, 128))
        indicator_size = 10
        vendor_dot = QGraphicsEllipseItem(
            -indicator_size / 2, -self.rect().height() / 2 - 5,
            indicator_size, indicator_size, self
        )
        vendor_dot.setBrush(QBrush(v_col))
        vendor_dot.setPen(QPen(v_col.darker(), 1))

        # Main label (hostname/vendor-octet)
        display = self.get_display_name()
        self.label = QGraphicsTextItem(display, self)
        self.label.setDefaultTextColor(QColor(255, 255, 255))
        self.label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        label_rect = self.label.boundingRect()
        self.label.setPos(-label_rect.width() / 2, size / 2 + 8)

        # Type badge
        type_badge = self.device_type.replace('_', ' ').title()
        self.type_label = QGraphicsTextItem(type_badge, self)
        self.type_label.setDefaultTextColor(QColor(200, 200, 200))
        self.type_label.setFont(QFont("Arial", 7))
        type_rect = self.type_label.boundingRect()
        self.type_label.setPos(-type_rect.width() / 2, size / 2 + 22)

        # Status dot (green online / red offline / gray unknown)
        status = (self.device_data.get('status') or '').lower()
        if status == 'online':
            status_color = QColor(0, 200, 0)
        elif status == 'offline':
            status_color = QColor(200, 0, 0)
        else:
            status_color = QColor(128, 128, 128)
        self.status_dot = QGraphicsEllipseItem(-5, -5, 10, 10, self)
        self.status_dot.setBrush(QBrush(status_color))
        self.status_dot.setPen(QPen(Qt.PenStyle.NoPen))
        self.status_dot.setPos(size / 3, -size / 3)

        # Draw above edges
        self.setZValue(1)

    def _setup_behavior(self):
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # Keep edges aligned while dragging nodes
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for edge in list(self.edges):
                edge.update_position()
        return super().itemChange(change, value)

    def add_edge(self, edge: "NetworkEdge"):
        self.edges.add(edge)

    # -------- Unified name + classifier --------

    def get_display_name(self) -> str:
        hostname = (self.device_data.get('hostname') or '').strip()
        vendor = (self.device_data.get('vendor') or '').strip()
        ip = (self.device_data.get('ip_address') or '').strip()

        if hostname and hostname != ip:
            return hostname[:30]
        if vendor and vendor.lower() != 'unknown' and ip:
            last_octet = ip.split('.')[-1]
            return f"{vendor}-{last_octet}"
        return ip.split('.')[-1] if ip else 'Node'

    def _classify_device_type(self) -> str:
        """Enhanced device classification for enterprise vendors"""
        device_type = (self.device_data.get('device_type') or '').lower()
        vendor = (self.device_data.get('vendor') or '').lower()
        hostname = (self.device_data.get('hostname') or '').lower()

        # If scanner already set a known type
        if device_type in self.NODE_TYPES:
            return device_type

        # Checkpoint
        if 'checkpoint' in vendor or 'checkpoint' in hostname:
            if 'firewall' in hostname or 'fw' in hostname:
                return 'checkpoint_firewall'
            return 'checkpoint_router'

        # VMware
        if 'vmware' in vendor or 'esxi' in hostname or 'vcenter' in hostname:
            if 'esxi' in hostname:
                return 'vmware_esxi'
            if 'vcenter' in hostname:
                return 'vmware_vcenter'
            return 'vmware_vm'

        # Cisco
        if 'cisco' in vendor or 'cisco' in hostname:
            if any(k in hostname for k in ['switch', 'catalyst', '2960', '3750', '3850']):
                return 'cisco_switch'
            if any(k in hostname for k in ['asa', 'firewall', 'fw']):
                return 'cisco_firewall'
            return 'cisco_router'

        # Rockwell PLC
        if 'rockwell' in vendor or 'allen' in vendor or 'plc' in hostname:
            return 'rockwell_plc'

        # T-Mobile router (common home gateways)
        if any(k in hostname for k in ['tmo', 'tmobile', 'g4ar']):
            return 'router'

        # Generic fallbacks by name
        if 'router' in hostname or 'gateway' in hostname:
            return 'router'
        if 'switch' in hostname:
            return 'switch'
        if 'firewall' in hostname or 'fw' in hostname:
            return 'firewall'
        if 'server' in hostname or hostname.startswith('srv-'):
            return 'server'
        if any(k in hostname for k in ['wifi', 'wireless', 'ap']):
            return 'wireless_ap'

        return 'unknown'


class NetworkEdge(QGraphicsLineItem):
    """Network connection line between nodes"""

    def __init__(self, node1: NetworkNode, node2: NetworkNode):
        super().__init__()
        self.node1 = node1
        self.node2 = node2

        # Style the connection line
        self._base_pen = QPen(QColor(100, 100, 100), 2, Qt.PenStyle.SolidLine)
        self._base_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(self._base_pen)

        # Draw behind nodes
        self.setZValue(0)
        self.setOpacity(0.7)

        # Register with nodes
        self.node1.add_edge(self)
        self.node2.add_edge(self)

        self.update_position()

    def update_position(self):
        p1: QPointF = self.node1.scenePos()
        p2: QPointF = self.node2.scenePos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())

    def reset_pen(self):
        self.setPen(self._base_pen)


class NetworkGraphWidget(QWidget):
    """Network graph with enhanced debugging"""

    node_selected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.nodes: Dict[str, NetworkNode] = {}
        self.edges: List[NetworkEdge] = []

        self._setup_ui()
        print("🚀 NetworkGraphWidget initialized")

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Controls
        controls = QGroupBox("📊 Network Visualization Controls")
        controls_layout = QHBoxLayout(controls)

        controls_layout.addWidget(QLabel("Layout:"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Static Grid", "Circular", "Random"])
        controls_layout.addWidget(self.layout_combo)

        zoom_in = QPushButton("🔍+ Zoom In")
        zoom_in.clicked.connect(lambda: self.view.scale(1.3, 1.3))
        controls_layout.addWidget(zoom_in)

        zoom_out = QPushButton("🔍- Zoom Out")
        zoom_out.clicked.connect(lambda: self.view.scale(0.7, 0.7))
        controls_layout.addWidget(zoom_out)

        fit_view = QPushButton("🎯 Fit View")
        fit_view.clicked.connect(self.fit_view)
        controls_layout.addWidget(fit_view)

        clear = QPushButton("🗑️ Clear")
        clear.clicked.connect(self.clear_graph)
        controls_layout.addWidget(clear)

        controls_layout.addStretch()
        layout.addWidget(controls)

        # Graphics view / scene
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-1000, -1000, 2000, 2000)
        self.scene.setBackgroundBrush(QBrush(QColor(30, 30, 30)))

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setStyleSheet("background-color: #1a1a1a; border: 2px solid #555;")
        layout.addWidget(self.view)

        # Debug status
        self.status_label = QLabel("Status: Ready - No nodes yet")
        self.status_label.setStyleSheet(
            "color: #ccc; padding: 5px; font-family: monospace;"
        )
        layout.addWidget(self.status_label)

        print("🎨 Scene and view created")

    def add_device(self, device_data: dict):
        """Add device with debugging + auto-connect - ONLY ACTIVE/ONLINE DEVICES"""
        ip = device_data.get('ip_address', 'unknown').strip()
        print(f"\n🔧 ADDING DEVICE: {ip}")
        print(f"   Data: {device_data}")

        if not ip:
            print("   ❌ No IP provided; skipping.")
            return

        # CRITICAL: Only add devices that are actually online/active
        status = device_data.get('status', '').lower()
        if status != 'online':
            print(f"   ⊘ SKIPPED: Device {ip} is {status} (not active) - not adding to topology")
            return

        if ip in self.nodes:
            print(f"   ⚠️ Device {ip} already exists! Skipping.")
            return

        # Create node
        try:
            node = NetworkNode(device_data)
            print("   ✅ Node object created")
        except Exception as e:
            print(f"   ❌ Failed to create node: {e}")
            return

        # Position node (simple circular layout around origin)
        node_count = len(self.nodes)
        if node_count == 0:
            x, y = 0.0, 0.0
        else:
            angle = node_count * (2 * math.pi / 8.0)  # step around circle of 8 slots
            radius = 200.0
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
        node.setPos(x, y)
        print(f"   📍 Positioned at ({x:.0f}, {y:.0f})")

        # Add to scene & index
        try:
            self.scene.addItem(node)
            self.nodes[ip] = node
            print("   ✅ Added to scene")
        except Exception as e:
            print(f"   ❌ Failed to add to scene: {e}")
            return

        # Auto-connect to existing nodes
        self._auto_connect(node)

        # Update UI
        self.status_label.setText(
            f"Status: {len(self.nodes)} nodes, {len(self.edges)} connections - Last: {ip}"
        )

        # Auto-fit the view after items settle
        QTimer.singleShot(100, self.fit_view)

        print("   🎯 DEVICE ADDED SUCCESSFULLY!")
        print(f"   Total nodes: {len(self.nodes)}")
        print(f"   Scene items: {len(self.scene.items())}")

    def _create_edge(self, node1: NetworkNode, node2: NetworkNode) -> bool:
        """Create edge between two nodes (avoid duplicates)"""
        if node1 is node2:
            return False
        for edge in self.edges:
            if ((edge.node1 is node1 and edge.node2 is node2) or
                (edge.node1 is node2 and edge.node2 is node1)):
                return False  # Already connected

        edge = NetworkEdge(node1, node2)
        self.edges.append(edge)
        self.scene.addItem(edge)
        return True

    def _auto_connect(self, new_node: NetworkNode):
        """Create realistic network connections based on actual topology"""
        new_ip = new_node.device_data.get('ip_address', '')
        new_subnet = '.'.join(new_ip.split('.')[:-1]) if new_ip else ''

        print(f"🔗 Connecting {new_node.get_display_name()} ({new_ip})")

        # Candidate routers (excluding self)
        routers = [
            node for node in self.nodes.values()
            if node.device_type == 'router' and node is not new_node
        ]

        if new_node.device_type == 'router':
            # Routers connect to other routers (prefer different subnets)
            for router in routers:
                router_ip = router.device_data.get('ip_address', '')
                router_subnet = '.'.join(router_ip.split('.')[:-1]) if router_ip else ''
                if router_subnet != new_subnet:
                    if self._create_edge(new_node, router):
                        print(f"   🌐 Router-to-router: "
                              f"{new_node.get_display_name()} <-> {router.get_display_name()}")
        else:
            # Non-router devices: connect to gateway in their subnet
            subnet_gateway: Optional[NetworkNode] = None
            for ip, node in self.nodes.items():
                if node is new_node:
                    continue
                node_subnet = '.'.join(ip.split('.')[:-1])
                if node_subnet == new_subnet:
                    last_octet = int(ip.split('.')[-1])
                    if last_octet in (1, 254) or node.device_type in ('router', 'firewall'):
                        subnet_gateway = node
                        break
            if subnet_gateway:
                if self._create_edge(new_node, subnet_gateway):
                    print(f"   🏠 Device-to-gateway: "
                          f"{new_node.get_display_name()} -> {subnet_gateway.get_display_name()}")
            elif routers:
                # Fallback: connect to any router
                closest_router = routers[0]
                if self._create_edge(new_node, closest_router):
                    print(f"   📡 Device-to-router: "
                          f"{new_node.get_display_name()} -> {closest_router.get_display_name()}")

    def _discover_realistic_connections_with_switch(self):
        """Discover connections with proper switch topology (optional helper)"""
        print("🔍 Analyzing network with switch topology...")

        # Clear existing connections
        for edge in self.edges[:]:
            self.scene.removeItem(edge)
        self.edges.clear()

        # Identify nodes
        tmo_router = None
        cisco_router = None
        switches = []
        wifi_devices = []

        for ip, node in self.nodes.items():
            h = (node.device_data.get('hostname') or '').lower()
            if 'tmo' in h or 'tmobile' in h:
                tmo_router = (ip, node)
                print(f"   📡 T-Mobile router: {ip}")
            elif 'c892' in h or (('cisco' in h) and 'router' in h):
                cisco_router = (ip, node)
                print(f"   🔶 Cisco router: {ip}")
            elif ('catalyst' in h or 'switch' in h or node.device_type == 'switch'):
                switches.append((ip, node))
                print(f"   🔌 Switch: {ip}")
            else:
                wifi_devices.append((ip, node))
                print(f"   📱 WiFi device: {ip}")

        # TMO Router <-> Cisco Router
        if tmo_router and cisco_router:
            if self._create_edge(tmo_router[1], cisco_router[1]):
                print(f"   🔗 TMO <-> Cisco: {tmo_router[0]} <-> {cisco_router[0]}")

        # TMO Router <-> Switches
        if tmo_router:
            for switch_ip, switch_node in switches:
                if self._create_edge(tmo_router[1], switch_node):
                    print(f"   🔗 TMO <-> Switch: {tmo_router[0]} <-> {switch_ip}")

        # WiFi devices <-> TMO Router (wireless)
        if tmo_router:
            for device_ip, device_node in wifi_devices:
                if self._create_edge(device_node, tmo_router[1]):
                    print(f"   📡 WiFi: {device_ip} -> {tmo_router[0]}")

        # Update status
        self.status_label.setText(
            f"Status: {len(self.nodes)} nodes, {len(self.edges)} connections (with switch)"
        )
        print(f"✅ Created proper switch topology with {len(self.edges)} connections")

    def _discover_realistic_connections(self):
        """Discover realistic connections based on subnets & gateways"""
        print("🔍 Analyzing network for realistic connections...")

        # Clear existing connections
        for edge in self.edges[:]:
            self.scene.removeItem(edge)
        self.edges.clear()

        # Group devices by subnet; identify routers
        subnets: Dict[str, List[tuple[str, NetworkNode]]] = {}
        routers: List[tuple[str, NetworkNode]] = []

        for ip, node in self.nodes.items():
            subnet = '.'.join(ip.split('.')[:-1])
            subnets.setdefault(subnet, []).append((ip, node))
            if node.device_type == 'router':
                routers.append((ip, node))

        print(f"   Found {len(subnets)} subnets: {list(subnets.keys())}")
        print(f"   Found {len(routers)} routers: {[r[0] for r in routers]}")

        # Connect devices in each subnet to a gateway
        for subnet, devices in subnets.items():
            print(f"   🏠 Processing subnet {subnet}.0/24 ({len(devices)} devices)")
            gateway: Optional[tuple[str, NetworkNode]] = None
            for ip, node in devices:
                last_octet = int(ip.split('.')[-1])
                if last_octet in (1, 254) or node.device_type in ('router', 'firewall'):
                    gateway = (ip, node)
                    print(f"      🚪 Found gateway: {ip}")
                    break

            if gateway:
                for ip, node in devices:
                    if ip != gateway[0] and node.device_type != 'router':
                        if self._create_edge(node, gateway[1]):
                            print(f"      🔗 {ip} -> {gateway[0]}")
            else:
                print(f"      ⚠️ No gateway found for subnet {subnet}")

        # Connect routers across different subnets (backbone)
        for i, (ip1, r1) in enumerate(routers):
            for ip2, r2 in routers[i + 1:]:
                if '.'.join(ip1.split('.')[:-1]) != '.'.join(ip2.split('.')[:-1]):
                    if self._create_edge(r1, r2):
                        print(f"   🌐 Router backbone: {ip1} <-> {ip2}")

        self.status_label.setText(
            f"Status: {len(self.nodes)} nodes, {len(self.edges)} realistic connections"
        )
        print(f"✅ Created {len(self.edges)} realistic connections")

    def _update_all_edges(self):
        for edge in self.edges:
            edge.update_position()

    def fit_view(self):
        """Fit view to show all content"""
        if self.nodes:
            items_rect = self.scene.itemsBoundingRect()
            print(f"🎯 Fitting view to: {items_rect}")
            padded = items_rect.adjusted(-100, -100, 100, 100)
            self.view.fitInView(padded, Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.view.fitInView(-500, -500, 1000, 1000, Qt.AspectRatioMode.KeepAspectRatio)
            print("🎯 No nodes - fitting to default area")

    def clear_graph(self):
        """Clear everything"""
        print("🗑️ Clearing graph")
        self.scene.clear()
        self.nodes.clear()
        self.edges.clear()
        self.status_label.setText("Status: Cleared - No nodes")


# Standalone test
def main():
    app = QApplication(sys.argv)

    widget = NetworkGraphWidget()
    widget.setWindowTitle("Network Graph Debug")
    widget.resize(1000, 700)
    widget.show()

    # Add test devices
    widget.add_device({'ip_address': '192.168.1.1', 'hostname': 'test-firewall', 'vendor': 'Checkpoint', 'status': 'online'})
    QTimer.singleShot(600, lambda: widget.add_device({'ip_address': '192.168.1.2', 'hostname': 'lab-switch', 'vendor': 'Cisco', 'status': 'online'}))
    QTimer.singleShot(1200, lambda: widget.add_device({'ip_address': '192.168.1.20', 'hostname': 'srv-research', 'vendor': 'Microsoft', 'status': 'online'}))
    QTimer.singleShot(1800, lambda: widget.add_device({'ip_address': '10.0.0.1', 'hostname': 'core-router', 'vendor': 'Cisco', 'status': 'online'}))

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

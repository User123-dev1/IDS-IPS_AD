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

        hostname = self.device_data.get('hostname', 'Unknown')
        vendor = self.device_data.get('vendor', 'Unknown')
        print(f"🎨 Created node: {self.get_display_name()} at (0,0) "
              f"[{self.device_type}] (vendor:{vendor}, hostname:{hostname})")

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
        services = self.device_data.get('services', [])

        # If scanner already set a known type (and it's not "unknown")
        if device_type in self.NODE_TYPES and device_type != 'unknown':
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

        # Cisco - Enhanced switch detection
        if 'cisco' in vendor or 'cisco' in hostname:
            # Check for switch indicators in hostname
            if any(k in hostname for k in ['switch', 'catalyst', '2960', '3750', '3850', 'sw-', 'sw_']):
                return 'cisco_switch'
            # Check for firewall indicators
            if any(k in hostname for k in ['asa', 'firewall', 'fw']):
                return 'cisco_firewall'
            # Check for router indicators
            if any(k in hostname for k in ['router', 'rtr', 'gateway', 'gw']):
                return 'cisco_router'
            # Default Cisco devices to switch if no clear indicator
            # (Cisco is most commonly deployed as switches)
            return 'cisco_switch'

        # Siemens - Usually industrial switches or PLCs
        if 'siemens' in vendor or 'siemens' in hostname:
            # Siemens industrial switches (SCALANCE series)
            if any(k in hostname for k in ['switch', 'scalance', 'ethernet']):
                return 'switch'
            # Siemens PLCs (S7 series)
            if any(k in hostname for k in ['plc', 's7-', 's7_']):
                return 'rockwell_plc'  # Use PLC type for industrial devices
            # Default Siemens to switch (common in industrial networks)
            return 'switch'

        # Rockwell PLC
        if 'rockwell' in vendor or 'allen' in vendor or 'plc' in hostname:
            return 'rockwell_plc'

        # T-Mobile router (common home gateways)
        if any(k in hostname for k in ['tmo', 'tmobile', 'g4ar']):
            return 'router'

        # Generic fallbacks by name
        if 'router' in hostname or 'gateway' in hostname or 'gw' in hostname:
            return 'router'
        if 'switch' in hostname or 'sw-' in hostname or 'sw_' in hostname:
            return 'switch'
        if 'firewall' in hostname or 'fw' in hostname:
            return 'firewall'
        if 'server' in hostname or hostname.startswith('srv-'):
            return 'server'
        if any(k in hostname for k in ['wifi', 'wireless', 'ap']):
            return 'wireless_ap'

        # Service-based classification (if hostname gives no clue)
        # Switches typically have SNMP, telnet/SSH, and HTTP/HTTPS
        if services:
            service_set = set(str(s).lower() for s in services)
            # Switch indicators: SNMP + multiple management protocols
            if any(s in service_set for s in ['snmp', '161', '162']):
                if any(s in service_set for s in ['telnet', 'ssh', '22', '23']):
                    # Has both SNMP and remote access = likely a switch
                    return 'switch'

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
        """
        Create realistic hierarchical network connections

        Topology discovery logic:
        1. Identify device role (router, switch, firewall, device)
        2. Find parent in network hierarchy
        3. Create connection to appropriate parent
        4. Build router-to-router backbone
        5. Connect switches to routers
        6. Connect devices to switches (or routers if no switch)
        """
        new_ip = new_node.device_data.get('ip_address', '')
        new_type = new_node.device_type
        new_subnet = self._get_subnet(new_ip)

        print(f"🔗 Auto-connecting {new_node.get_display_name()} ({new_ip}) [{new_type}]")

        # === STEP 1: Router connections (backbone) ===
        if 'router' in new_type or 'firewall' in new_type:
            self._connect_router_node(new_node, new_ip, new_subnet)
            return

        # === STEP 2: Switch connections ===
        if 'switch' in new_type:
            self._connect_switch_node(new_node, new_ip, new_subnet)
            return

        # === STEP 3: End device connections ===
        self._connect_end_device(new_node, new_ip, new_subnet)

    def _connect_router_node(self, router_node: NetworkNode, router_ip: str, router_subnet: str):
        """Connect routers - form backbone between different subnets"""
        print(f"   🌐 Connecting router/firewall: {router_node.get_display_name()}")

        # Find other routers, prefer cross-subnet connections
        other_routers = [
            (ip, node) for ip, node in self.nodes.items()
            if node is not router_node and ('router' in node.device_type or 'firewall' in node.device_type)
        ]

        if not other_routers:
            print(f"      ℹ️ First router - no connections yet")
            return

        # Connect to routers in different subnets (WAN links)
        connected = False
        for other_ip, other_router in other_routers:
            other_subnet = self._get_subnet(other_ip)
            if other_subnet != router_subnet:
                if self._create_edge(router_node, other_router):
                    print(f"      ✅ Router backbone: {router_ip} <-> {other_ip} (cross-subnet)")
                    connected = True

        # If no cross-subnet routers, connect to first available router
        if not connected and other_routers:
            first_router_ip, first_router = other_routers[0]
            if self._create_edge(router_node, first_router):
                print(f"      ✅ Router link: {router_ip} <-> {first_router_ip} (same-subnet)")

    def _connect_switch_node(self, switch_node: NetworkNode, switch_ip: str, switch_subnet: str):
        """Connect switch to upstream router/firewall in same subnet"""
        print(f"   🔌 Connecting switch: {switch_node.get_display_name()}")

        # Find routers/firewalls in the same subnet
        upstream_devices = [
            (ip, node) for ip, node in self.nodes.items()
            if node is not switch_node
               and self._get_subnet(ip) == switch_subnet
               and ('router' in node.device_type or 'firewall' in node.device_type)
        ]

        if upstream_devices:
            # Connect to first router/firewall in subnet
            upstream_ip, upstream_node = upstream_devices[0]
            if self._create_edge(switch_node, upstream_node):
                print(f"      ✅ Switch → Router: {switch_ip} -> {upstream_ip}")
                return

        # Fallback: connect to any router if no same-subnet router found
        any_router = next(
            ((ip, node) for ip, node in self.nodes.items()
             if node is not switch_node and 'router' in node.device_type),
            None
        )
        if any_router:
            router_ip, router_node = any_router
            if self._create_edge(switch_node, router_node):
                print(f"      ✅ Switch → Router (cross-subnet): {switch_ip} -> {router_ip}")
        else:
            print(f"      ⚠️ No router found for switch")

    def _connect_end_device(self, device_node: NetworkNode, device_ip: str, device_subnet: str):
        """Connect end device to switch (preferred) or router"""
        print(f"   📱 Connecting device: {device_node.get_display_name()}")

        # Priority 1: Connect to switch in same subnet
        switches_in_subnet = [
            (ip, node) for ip, node in self.nodes.items()
            if node is not device_node
               and self._get_subnet(ip) == device_subnet
               and 'switch' in node.device_type
        ]

        if switches_in_subnet:
            switch_ip, switch_node = switches_in_subnet[0]
            if self._create_edge(device_node, switch_node):
                print(f"      ✅ Device → Switch: {device_ip} -> {switch_ip}")
                return

        # Priority 2: Connect to router/firewall in same subnet
        routers_in_subnet = [
            (ip, node) for ip, node in self.nodes.items()
            if node is not device_node
               and self._get_subnet(ip) == device_subnet
               and ('router' in node.device_type or 'firewall' in node.device_type)
        ]

        if routers_in_subnet:
            router_ip, router_node = routers_in_subnet[0]
            if self._create_edge(device_node, router_node):
                print(f"      ✅ Device → Router: {device_ip} -> {router_ip}")
                return

        # Priority 3: Connect to gateway (.1 or .254 in same subnet)
        gateway = self._find_gateway_in_subnet(device_subnet, device_ip)
        if gateway:
            gw_ip, gw_node = gateway
            if self._create_edge(device_node, gw_node):
                print(f"      ✅ Device → Gateway: {device_ip} -> {gw_ip}")
                return

        # Priority 4: Connect to any switch
        any_switch = next(
            ((ip, node) for ip, node in self.nodes.items()
             if node is not device_node and 'switch' in node.device_type),
            None
        )
        if any_switch:
            switch_ip, switch_node = any_switch
            if self._create_edge(device_node, switch_node):
                print(f"      ✅ Device → Switch (any): {device_ip} -> {switch_ip}")
                return

        # Priority 5: Connect to any router
        any_router = next(
            ((ip, node) for ip, node in self.nodes.items()
             if node is not device_node and 'router' in node.device_type),
            None
        )
        if any_router:
            router_ip, router_node = any_router
            if self._create_edge(device_node, router_node):
                print(f"      ✅ Device → Router (any): {device_ip} -> {router_ip}")
                return

        print(f"      ⚠️ No upstream device found for {device_ip}")

    def _get_subnet(self, ip: str) -> str:
        """Extract subnet from IP (e.g., '192.168.1.10' -> '192.168.1')"""
        return '.'.join(ip.split('.')[:-1]) if ip else ''

    def _find_gateway_in_subnet(self, subnet: str, exclude_ip: str) -> Optional[tuple[str, NetworkNode]]:
        """Find likely gateway (.1 or .254) in subnet"""
        for ip, node in self.nodes.items():
            if ip == exclude_ip:
                continue
            if self._get_subnet(ip) == subnet:
                last_octet = int(ip.split('.')[-1])
                if last_octet in (1, 254):
                    return (ip, node)
        return None

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
        """
        Rebuild all connections using hierarchical topology discovery

        Process:
        1. Clear existing connections
        2. Categorize devices by role
        3. Build router backbone (router-to-router)
        4. Connect switches to routers
        5. Connect devices to switches/routers
        """
        print("🔍 Discovering realistic hierarchical topology...")

        # Clear existing edges
        for edge in self.edges[:]:
            self.scene.removeItem(edge)
        self.edges.clear()

        # Categorize devices
        routers = []
        switches = []
        devices = []

        for ip, node in self.nodes.items():
            if 'router' in node.device_type or 'firewall' in node.device_type:
                routers.append((ip, node))
            elif 'switch' in node.device_type:
                switches.append((ip, node))
            else:
                devices.append((ip, node))

        print(f"   📊 Found: {len(routers)} routers, {len(switches)} switches, {len(devices)} devices")

        # === PHASE 1: Router backbone (cross-subnet connections) ===
        print("   🌐 Phase 1: Building router backbone...")
        router_count = 0
        for i, (ip1, r1) in enumerate(routers):
            subnet1 = self._get_subnet(ip1)
            for ip2, r2 in routers[i + 1:]:
                subnet2 = self._get_subnet(ip2)
                # Connect routers in different subnets
                if subnet1 != subnet2:
                    if self._create_edge(r1, r2):
                        print(f"      ✅ {ip1} <-> {ip2}")
                        router_count += 1
        print(f"   ✅ Created {router_count} router backbone connections")

        # === PHASE 2: Switch connections to routers ===
        print("   🔌 Phase 2: Connecting switches to routers...")
        switch_count = 0
        for switch_ip, switch_node in switches:
            switch_subnet = self._get_subnet(switch_ip)

            # Find router in same subnet
            same_subnet_router = next(
                ((ip, node) for ip, node in routers if self._get_subnet(ip) == switch_subnet),
                None
            )

            if same_subnet_router:
                router_ip, router_node = same_subnet_router
                if self._create_edge(switch_node, router_node):
                    print(f"      ✅ Switch {switch_ip} -> Router {router_ip}")
                    switch_count += 1
            elif routers:
                # Fallback: connect to first router
                router_ip, router_node = routers[0]
                if self._create_edge(switch_node, router_node):
                    print(f"      ✅ Switch {switch_ip} -> Router {router_ip} (cross-subnet)")
                    switch_count += 1
        print(f"   ✅ Connected {switch_count} switches")

        # === PHASE 3: Device connections (to switches or routers) ===
        print("   📱 Phase 3: Connecting end devices...")
        device_count = 0
        for device_ip, device_node in devices:
            device_subnet = self._get_subnet(device_ip)

            # Try to connect to switch in same subnet first
            same_subnet_switch = next(
                ((ip, node) for ip, node in switches if self._get_subnet(ip) == device_subnet),
                None
            )

            if same_subnet_switch:
                switch_ip, switch_node = same_subnet_switch
                if self._create_edge(device_node, switch_node):
                    print(f"      ✅ Device {device_ip} -> Switch {switch_ip}")
                    device_count += 1
                    continue

            # Try router in same subnet
            same_subnet_router = next(
                ((ip, node) for ip, node in routers if self._get_subnet(ip) == device_subnet),
                None
            )

            if same_subnet_router:
                router_ip, router_node = same_subnet_router
                if self._create_edge(device_node, router_node):
                    print(f"      ✅ Device {device_ip} -> Router {router_ip}")
                    device_count += 1
                    continue

            # Fallback: any switch or router
            if switches:
                switch_ip, switch_node = switches[0]
                if self._create_edge(device_node, switch_node):
                    print(f"      ✅ Device {device_ip} -> Switch {switch_ip} (any)")
                    device_count += 1
            elif routers:
                router_ip, router_node = routers[0]
                if self._create_edge(device_node, router_node):
                    print(f"      ✅ Device {device_ip} -> Router {router_ip} (any)")
                    device_count += 1

        print(f"   ✅ Connected {device_count} devices")

        # Update status
        self.status_label.setText(
            f"Status: {len(self.nodes)} nodes, {len(self.edges)} hierarchical connections"
        )
        print(f"✅ Topology complete: {len(self.edges)} total connections")

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
    widget.add_device(
        {'ip_address': '192.168.1.1', 'hostname': 'test-firewall', 'vendor': 'Checkpoint', 'status': 'online'})
    QTimer.singleShot(600, lambda: widget.add_device(
        {'ip_address': '192.168.1.2', 'hostname': 'lab-switch', 'vendor': 'Cisco', 'status': 'online'}))
    QTimer.singleShot(1200, lambda: widget.add_device(
        {'ip_address': '192.168.1.20', 'hostname': 'srv-research', 'vendor': 'Microsoft', 'status': 'online'}))
    QTimer.singleShot(1800, lambda: widget.add_device(
        {'ip_address': '10.0.0.1', 'hostname': 'core-router', 'vendor': 'Cisco', 'status': 'online'}))

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
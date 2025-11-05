# IDS/IPS Threat Simulation Guide

## Overview

This guide explains how to test the IDS/IPS capabilities of the OT Security System by simulating various network attacks from a separate PC connected to the monitored network.

## System Capabilities

### Intrusion Detection System (IDS)
- Real-time network traffic monitoring
- Anomaly detection based on learned baselines
- New device detection
- Protocol analysis
- Behavioral analysis

### Intrusion Prevention System (IPS)
- Port scan detection
- Brute force attack detection
- DoS/DDoS attack detection
- OT/ICS protocol intrusion detection
- External C2 communication detection
- Automatic alerting to system administrators

## Prerequisites

### Monitored Network (Target)
- IDS/IPS application running on monitoring PC
- Live network monitoring enabled
- Baseline learning completed (or detection mode active)

### Attack Simulation PC (Attacker)
- Connected to the same network as the monitored system
- Network testing tools installed (see tools section below)
- **Important**: This PC should be isolated or authorized for testing only

## Simulation Scenarios

### 1. New Device Detection Test

**Objective**: Test if the system detects when a new device connects to the network

**Steps**:
1. Ensure the attack PC has never been on this network before (or clear its entry from the baseline)
2. Connect the PC to the network
3. Generate some network traffic (ping, browse web, etc.)

**Expected Detection**:
- **Alert Level**: HIGH
- **Category**: NEW_DEVICE
- **Description**: "🆕 NEW DEVICE CONNECTED: [IP] - Not in baseline, requires investigation"
- **Action**: System admin should receive alert to verify authorization

### 2. Port Scanning Attack

**Objective**: Detect reconnaissance activities

**Tools**: nmap, masscan, or custom scanner

**Attack Command**:
```bash
# Using nmap
nmap -p 1-1000 [target_subnet]

# Example: Scan entire subnet
nmap -p 1-1000 192.168.1.0/24

# Aggressive scan
nmap -A [target_ip]
```

**Expected Detection**:
- **Alert Level**: CRITICAL
- **Category**: PORT_SCAN
- **Description**: "🚨 ATTACK DETECTED: Potential port scanning from [attacker_IP]"
- **Threshold**: >100 packets per minute from single source
- **Recommended Action**: BLOCK IP address

### 3. Brute Force Attack

**Objective**: Detect credential guessing attacks

**Tools**: hydra, medusa, ncrack, or custom script

**Attack Commands**:
```bash
# SSH brute force using hydra
hydra -l admin -P /path/to/passwords.txt ssh://[target_ip]

# RDP brute force
hydra -l administrator -P passwords.txt rdp://[target_ip]

# FTP brute force
hydra -l ftp -P passwords.txt ftp://[target_ip]
```

**Expected Detection**:
- **Alert Level**: CRITICAL
- **Category**: BRUTE_FORCE
- **Description**: "🚨 ATTACK DETECTED: Brute force attack from [IP] targeting port [port]"
- **Threshold**: >20 authentication attempts per minute
- **Recommended Action**: BLOCK IMMEDIATELY

### 4. OT/ICS Protocol Intrusion

**Objective**: Detect unauthorized access to industrial control systems

**Tools**: modbus client, S7 client, or scapy

**Attack Commands**:
```bash
# Modbus scanning (port 502)
nmap -p 502 --script modbus-discover [target_ip]

# S7 protocol scan (port 102)
python s7_scan.py [target_ip]

# Simple port connection test
nc [target_ip] 502  # Modbus
nc [target_ip] 102  # Siemens S7
nc [target_ip] 44818  # EtherNet/IP
nc [target_ip] 20000  # DNP3
nc [target_ip] 4840  # OPC UA
```

**Python Script for Modbus Testing**:
```python
import socket

def test_modbus_connection(target_ip, port=502):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((target_ip, port))
        print(f"Connected to {target_ip}:{port}")
        sock.close()
    except Exception as e:
        print(f"Connection failed: {e}")

test_modbus_connection("192.168.1.100")
```

**Expected Detection**:
- **Alert Level**: CRITICAL
- **Category**: OT_ATTACK
- **Description**: "🚨 CRITICAL: OT/ICS protocol access from [attacker_IP] to [target]:[port]"
- **Triggered on**: Any traffic to ports 502, 102, 44818, 2222, 20000, 4840
- **Recommended Action**: INVESTIGATE IMMEDIATELY - Potential sabotage attempt

### 5. Denial of Service (DoS) Attack

**Objective**: Detect network flooding attacks

**Tools**: hping3, slowloris, or custom flood scripts

**Attack Commands**:
```bash
# SYN flood using hping3
sudo hping3 -S -p 80 --flood [target_ip]

# UDP flood
sudo hping3 --udp -p 80 --flood [target_ip]

# ICMP flood
sudo hping3 --icmp --flood [target_ip]
```

**Python Script for Controlled DoS**:
```python
import socket
import time

def controlled_dos(target_ip, target_port, duration_seconds):
    """Controlled DoS for testing - sends high rate of packets"""
    end_time = time.time() + duration_seconds
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while time.time() < end_time:
        try:
            sock.connect((target_ip, target_port))
            sock.send(b"GET / HTTP/1.1\r\n\r\n")
        except:
            pass

    sock.close()

# Test for 10 seconds
controlled_dos("192.168.1.100", 80, 10)
```

**Expected Detection**:
- **Alert Level**: CRITICAL
- **Category**: DOS_ATTACK
- **Description**: "🚨 ATTACK DETECTED: Potential DoS/DDoS attack from [IP]"
- **Threshold**: >500 packets per minute from single source
- **Recommended Action**: BLOCK IMMEDIATELY - Network flooding detected

### 6. Unusual Protocol Detection

**Objective**: Detect unexpected network protocols

**Tools**: scapy, custom packet crafting

**Python Script**:
```python
from scapy.all import *

def send_unusual_protocol(target_ip):
    # Send unusual SCTP packet
    packet = IP(dst=target_ip)/SCTP()
    send(packet)

    # Send raw protocol packet
    packet = IP(dst=target_ip, proto=253)/Raw(load="test")
    send(packet)

send_unusual_protocol("192.168.1.100")
```

**Expected Detection**:
- **Alert Level**: LOW to HIGH (HIGH if industrial protocol)
- **Category**: UNUSUAL_PROTOCOL
- **Description**: "Unusual protocol detected" or "⚠️ Unexpected industrial protocol detected"

## Setting Up the IDS/IPS for Testing

### 1. Start the Application
```bash
cd /path/to/IDS-IPS_AD
python src/main.py
```

### 2. Enable Live Monitoring

1. Navigate to the "Live Dashboard" or "Network Monitor" tab
2. Select the network interface to monitor
3. Choose learning mode:
   - **Learning Mode**: Establish a baseline (run for 5-10 minutes with normal traffic)
   - **Detection Mode**: Active threat detection (use after baseline is established)
4. Click "Start Monitoring"

### 3. Configure Alert Rules

Edit `config/alert_rules.json` to customize detection rules:
```json
{
  "enabled": true,
  "rules": [
    {
      "id": "block_suspicious_ip",
      "name": "Block Suspicious IP",
      "type": "ip_blacklist",
      "enabled": true,
      "severity": "HIGH",
      "ips": ["suspicious_ip_here"]
    }
  ]
}
```

## Monitoring Alerts

### Real-Time Alert Display

Alerts appear in:
1. **Live Dashboard**: Recent Anomalies section
2. **Console/Logs**: Detailed logging with timestamps
3. **System Notifications**: Critical alerts trigger system notifications

### Alert Severity Levels

- **LOW**: Informational, requires monitoring
- **MEDIUM**: Suspicious activity, requires investigation
- **HIGH**: Confirmed anomaly, immediate attention needed
- **CRITICAL**: Active attack detected, immediate action required

## Automatic Response Actions

### Current Capabilities (Detection)
✅ Real-time alerting
✅ Detailed logging
✅ Administrator notifications
✅ Anomaly tracking and reporting

### Recommended Manual Actions

When an alert is triggered:

1. **NEW_DEVICE**:
   - Verify device authorization
   - Add to asset inventory if legitimate
   - Quarantine if unauthorized

2. **PORT_SCAN / BRUTE_FORCE**:
   - Add firewall rule to block attacker IP
   - Review access logs
   - Check for successful breaches

3. **OT_ATTACK**:
   - Immediately isolate affected OT devices
   - Investigate attack source
   - Review OT network segmentation

4. **DOS_ATTACK**:
   - Implement rate limiting
   - Block attacker IP at network edge
   - Contact ISP if external attack

## Automated Asset Inventory Updates

### How It Works

New devices discovered during live monitoring are:
1. Automatically detected when they generate network traffic
2. Analyzed for device type (OT vs IT)
3. Classified by vendor and protocol
4. Can be automatically added to the asset inventory

### Enabling Auto-Add

The system includes a method `get_new_devices_for_inventory()` that retrieves:
- Devices discovered in the last N minutes
- Device classification (OT/IT)
- Protocols and ports detected
- Vendor identification

Integration code (to be added to main window):
```python
# Periodically check for new devices
new_devices = network_monitor.get_new_devices_for_inventory(since_minutes=5)
for device in new_devices:
    asset_manager.add_device_to_inventory(device)
```

## Safety and Legal Considerations

⚠️ **IMPORTANT WARNINGS**:

1. **Authorization Required**: Only perform penetration testing on networks you own or have written permission to test
2. **Isolated Environment**: Use a test network isolated from production systems
3. **Controlled Testing**: Start with low-intensity tests and gradually increase
4. **Document Everything**: Keep records of all testing activities
5. **Backup First**: Ensure all critical systems are backed up before testing
6. **Notify Stakeholders**: Inform all relevant parties before testing
7. **Legal Compliance**: Ensure compliance with local laws and regulations

## Troubleshooting

### IDS Not Detecting Attacks

1. **Check Monitoring Status**: Ensure live monitoring is active
2. **Verify Interface**: Correct network interface selected
3. **Check Permissions**: Application may need elevated privileges (root/admin) for packet capture
4. **Review Thresholds**: Attack may be below detection thresholds
5. **Baseline Issues**: Ensure baseline was properly established

### False Positives

1. **Adjust Thresholds**: Modify detection thresholds in code
2. **Whitelist Known Devices**: Add legitimate devices to baseline
3. **Custom Rules**: Create exceptions in alert rules

### Performance Issues

1. **High Traffic Networks**: May need to optimize packet processing
2. **Resource Constraints**: Ensure adequate CPU and memory
3. **Database Size**: Periodically clean old anomaly records

## Advanced Testing

### Multi-Vector Attack Simulation

Combine multiple attacks simultaneously:
```bash
# Terminal 1: Port scan
nmap -p 1-1000 192.168.1.0/24 &

# Terminal 2: Brute force
hydra -l admin -P passwords.txt ssh://192.168.1.10 &

# Terminal 3: DoS
hping3 -S --flood 192.168.1.10
```

### Stealthy Attacks

Test detection of slow, low-intensity attacks:
```bash
# Slow port scan (harder to detect)
nmap -T1 -p 1-1000 192.168.1.10

# Slow brute force
hydra -t 1 -w 30 -l admin -P passwords.txt ssh://192.168.1.10
```

## Reporting

Generate attack detection reports:
1. Navigate to "Reports" section
2. Select date range for testing period
3. Export anomaly report (JSON/CSV)
4. Review detection accuracy and response times

## Conclusion

This IDS/IPS system provides comprehensive threat detection for OT/IT environments. Regular testing ensures the system remains effective against evolving threats. Always follow security best practices and legal requirements when performing security testing.

For questions or issues, refer to the main documentation or contact the security team.

---

**Last Updated**: 2025-11-05
**Version**: 1.0

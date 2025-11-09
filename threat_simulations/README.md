# Threat Simulation Scripts for IDS/IPS Testing

## Overview

These scripts simulate various cyber attacks to test the IDS/IPS detection capabilities. **Run these scripts from a DIFFERENT PC on the same network** as your IDS/IPS system.

---

## ⚠️ IMPORTANT WARNINGS

1. **ONLY run these on networks you own or have written permission to test**
2. **These are real attack simulations** - they may trigger security alerts
3. **Do NOT run on production networks** without proper authorization
4. **Use a test/lab environment**
5. **Inform network administrators** before testing

**Unauthorized use is illegal and unethical!**

---

## Prerequisites

### Python Scripts Requirements:
```bash
pip install scapy requests paramiko
```

### PowerShell Scripts Requirements:
- Windows PowerShell 5.1 or later
- Administrator privileges for some tests

---

## Configuration

**Edit the TARGET_IP in each script to match your IDS/IPS monitored system:**

```python
TARGET_IP = "192.168.1.50"  # Change to your target
```

---

## Threat Simulation Scripts

### 1. Port Scanning Attack
### 2. Brute Force Attack
### 3. DoS/DDoS Attack
### 4. Reconnaissance Attack
### 5. Network Flooding
### 6. Combined Attack Scenario

---

## Expected IDS/IPS Behavior

For each simulation, the IDS/IPS should:

✅ **Detect** - Identify the attack pattern
✅ **Alert** - Create anomaly alert with details
✅ **Prevent** - (IPS mode) Block or rate-limit malicious traffic
✅ **Log** - Record attack details for analysis

---

## Detection Layers

Your IDS/IPS has 3 detection layers:

1. **Rule-Based** - Pattern matching (port scans, brute force)
2. **Baseline Anomaly** - Unusual behavior detection
3. **ML Detection** - Flow-based ML analysis (90.6% accuracy)

Most attacks should be detected by **multiple layers**!

---

## Usage Instructions

### Step 1: Set Up Test Environment

**On IDS/IPS PC (192.168.1.10):**
```bash
# Start IDS/IPS application
cd C:\Users\otlaptop\PycharmProjects\IDS-IPS_AD
python src/main.py

# Go to "Network Monitor" tab
# Click "Start Monitoring"
```

### Step 2: Run Simulations (From Different PC)

**On Attacker PC (192.168.1.100):**
```bash
# Python version
python threat_simulation_1_port_scan.py

# OR PowerShell version
.\ThreatSimulation-PortScan.ps1
```

### Step 3: Monitor Detections

Watch the IDS/IPS "Network Monitor" tab for:
- Real-time anomaly alerts
- Attack classifications
- Threat levels (CRITICAL/HIGH/MEDIUM/LOW)
- Source IP, attack type, confidence

---

## Testing Checklist

| Attack Type | Script | Expected Detection | Layer |
|-------------|--------|-------------------|-------|
| Port Scan | threat_simulation_1_port_scan.py | 🚨 Port scanning detected | Rule-based + ML |
| Brute Force SSH | threat_simulation_2_brute_force.py | 🚨 Brute force attempt | Rule-based |
| DoS Attack | threat_simulation_3_dos.py | 🚨 High packet rate | Rule-based + ML |
| Reconnaissance | threat_simulation_4_recon.py | 🚨 Network scanning | Baseline + ML |
| SYN Flood | threat_simulation_5_syn_flood.py | 🚨 DoS/DDoS attack | Rule-based + ML |
| Combined | threat_simulation_6_combined.py | 🚨 Multiple attacks | All layers |

---

## Next Steps

1. Review individual script files for detailed usage
2. Start with port scan (least aggressive)
3. Monitor IDS/IPS dashboard during each test
4. Review detection statistics after testing
5. Adjust detection thresholds if needed

---

## Troubleshooting

### No Detection Occurring

**Possible Causes:**
1. Target IP incorrect
2. Firewall blocking traffic
3. IDS/IPS not monitoring
4. Network isolation

**Solutions:**
1. Verify network connectivity: `ping 192.168.1.50`
2. Check IDS/IPS is running and monitoring
3. Ensure both PCs on same subnet
4. Disable Windows Firewall temporarily for testing

### False Positives

If normal traffic is flagged:
1. Review detection thresholds in `src/scanner/network_monitor.py`
2. Whitelist known-good IPs
3. Adjust ML threat levels

### Script Errors

**Python:**
```bash
# Missing dependencies
pip install scapy requests paramiko

# Permission errors (Linux/Mac)
sudo python threat_simulation_1_port_scan.py
```

**PowerShell:**
```powershell
# Execution policy
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Run as Administrator
# Right-click PowerShell → "Run as Administrator"
```

### ❌ "MAC Address to reach destination not found" Error

This error occurs in **threat_simulation_3_syn_flood.py** when Scapy cannot find the target IP on the network.

**Root Cause:**
- The target IP (default: 192.168.1.50) is not reachable from your machine
- Scapy needs to resolve the IP to a MAC address via ARP
- If the IP doesn't exist or is on a different network segment, the error occurs

**SOLUTIONS:**

**Option 1: Use Localhost (Easiest)**
```python
# Edit threat_simulation_3_syn_flood.py, line 26:
TARGET_IP = "127.0.0.1"  # Attack your own machine
```
Then run the IDS/IPS on the same machine and monitor localhost traffic.

**Option 2: Use a Reachable IP**
```bash
# First, find a reachable IP on your network
ping 192.168.1.10  # Test connectivity

# If ping works, edit the script:
TARGET_IP = "192.168.1.10"  # IP that responded to ping
```

**Option 3: Run on Same Network Segment**
- Ensure both attacker and target PCs are on the same subnet (e.g., 192.168.1.x)
- Check with: `ipconfig` (Windows) or `ip addr` (Linux)
- Both should have IPs like 192.168.1.x with same subnet mask

**Option 4: Specify Network Interface**
```python
# Edit threat_simulation_3_syn_flood.py, line 33:
INTERFACE = "eth0"  # Linux
INTERFACE = "Wi-Fi"  # Windows
INTERFACE = "en0"   # macOS
```

**Verify Before Running:**
The updated script now includes automatic diagnostics! Run it and check:
```bash
sudo python threat_simulation_3_syn_flood.py

# You'll see:
# - Available network interfaces
# - Route to target
# - Connectivity test (ping)
# - Clear error messages if issues detected
```

**Quick Test:**
```bash
# Test with localhost (always works):
sudo python threat_simulation_3_syn_flood.py
# When prompted, check that TARGET_IP is 127.0.0.1
# This will work even without network access
```

---

## Safety Notes

- Start with least aggressive tests (port scan)
- Monitor system resources during DoS tests
- Stop immediately if system becomes unstable
- Document all testing activities
- Obtain written authorization before testing

---

## Report Results

After testing, generate report:

**In IDS/IPS Application:**
1. Go to "Reports" tab
2. Click "Generate Security Report"
3. Review detected attacks
4. Check detection accuracy
5. Note any missed attacks or false positives

---

See individual script files for detailed implementation and usage instructions.

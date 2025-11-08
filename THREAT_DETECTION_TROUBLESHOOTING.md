# IDS/IPS Not Detecting Threats - Troubleshooting Guide

## Problem

After running the three threat simulation scripts from a different PC on the same network, **nothing was detected** by the ML detector or network monitor. Not a single detection.

## Root Cause

**Network monitoring was not started!** The IDS/IPS application requires you to manually start network monitoring - it does not auto-start.

---

## Solution: How to Start Network Monitoring

### Step 1: Run Application as Administrator

**CRITICAL:** Packet capture requires elevated privileges!

#### Windows:
```bash
# Right-click on Command Prompt or PowerShell → "Run as Administrator"
# Then run:
cd C:\Users\otlaptop\PycharmProjects\IDS-IPS_AD
.venv\Scripts\activate
python src/main.py
```

#### Linux:
```bash
sudo python src/main.py
```

**Without administrator/root privileges, packet capture WILL NOT WORK!**

---

### Step 2: Navigate to Network Monitor Tab

1. Open the IDS/IPS application
2. Click on the **" Network Monitor"** tab at the top

You should see two buttons:
- 🎓 **Start Learning Mode**
- 🚨 **Start Detection Mode**

---

### Step 3: Choose Monitoring Mode

#### Option A: Start Learning Mode (Recommended First)

**Click:** 🎓 **Start Learning Mode**

**Purpose:**
- Learns normal network behavior for 30-60 seconds
- Establishes baseline for what's "normal"
- Better detection accuracy after baseline is established

**When to use:**
- First time running the IDS/IPS
- Want to establish a clean baseline
- Need to learn new devices on network

#### Option B: Start Detection Mode

**Click:** 🚨 **Start Detection Mode**

**Purpose:**
- Immediately starts detecting threats
- Does NOT learn baseline (uses existing or none)
- More aggressive detection

**When to use:**
- After learning baseline
- For immediate threat detection
- Testing threat simulations

---

### Step 4: Verify Monitoring is Active

After clicking a start button, you should see:

**Status indicator changes to:**
```
✓ Monitoring: ACTIVE (LEARNING MODE)
```
or
```
✓ Monitoring: ACTIVE (DETECTION MODE)
```

**Console/Log output shows:**
```
✓ Real-time monitoring started
• Hybrid ML models: Loaded
• IDS/IPS engine: Active
• Network interface: <interface_name>
```

---

### Step 5: Run Threat Simulations

**NOW** run your threat simulations from the different PC:

```bash
# From the attacking PC (different machine on same network):
cd threat_simulations/

# Port Scan
python threat_simulation_1_port_scan.py

# Brute Force
python threat_simulation_2_brute_force.py

# SYN Flood (requires admin/root)
sudo python threat_simulation_3_syn_flood.py
```

---

## Expected Detections

### 1. Port Scan Detection

**Expected Alert:**
```
🚨 THREAT DETECTED
Severity: HIGH
Category: PORT_SCAN
Description: Rapid connection attempts detected from <attacker_IP>
ML Confidence: 85-95%
Rule Match: Port scan pattern (>50 connections/min)
```

**Visible in:**
- Network Monitor → Anomalies table
- Detection log
- Statistics counters increment

### 2. Brute Force Detection

**Expected Alert:**
```
🚨 THREAT DETECTED
Severity: CRITICAL
Category: BRUTE_FORCE
Description: Multiple authentication attempts to port 22 from <attacker_IP>
ML Confidence: 90-98%
Rule Match: >20 connection attempts/min to SSH
```

### 3. SYN Flood Detection

**Expected Alert:**
```
🚨 THREAT DETECTED
Severity: CRITICAL
Category: DOS_ATTACK
Description: High volume SYN packets detected from <attacker_IP>
ML Confidence: 95-99%
Rule Match: >500 packets/min
```

---

## Troubleshooting: Why Am I Still Not Seeing Detections?

### Issue 1: No Administrator Privileges

**Symptom:**
- Monitoring fails to start
- Error message: "Failed to start network monitoring"
- Console error: "Permission denied"

**Fix:**
```bash
# Windows: Run as Administrator
# Linux: Use sudo
sudo python src/main.py
```

### Issue 2: Wrong Network Interface

**Symptom:**
- Monitoring starts but no packets captured
- Device count stays at 0
- No traffic statistics

**Fix:**
1. Stop monitoring
2. Check your network interfaces:
```bash
# Windows
ipconfig

# Linux
ip addr show
```
3. Identify the correct interface (the one connected to the network with the attacking PC)
4. Modify the code if needed to specify interface

**Check:** `src/scanner/network_monitor.py` - The `start_monitoring()` method should auto-detect the interface.

### Issue 3: Npcap/WinPcap Not Installed (Windows)

**Symptom:**
- Error: "Npcap not found"
- Packet capture fails

**Fix:**
1. Download Npcap: https://npcap.com/#download
2. Install with "WinPcap API-compatible Mode" checked
3. Restart application

### Issue 4: Firewall Blocking Traffic

**Symptom:**
- Threat simulations can't connect to target
- Connection timeout errors

**Fix:**
1. Temporarily disable firewall on TARGET PC (the one running IDS/IPS)
2. Or add firewall rules to allow traffic on test ports
3. Re-run threat simulations

### Issue 5: Target IP Incorrect

**Symptom:**
- Threat simulations run but no detections
- Attacking wrong IP

**Fix:**
1. On IDS/IPS PC, find your IP:
```bash
# Windows
ipconfig

# Linux
ip addr show
```

2. Update threat simulation scripts with correct IP:
```python
# In threat_simulation_*.py
TARGET_IP = "192.168.1.50"  # ← Change this to YOUR IDS/IPS PC's IP
```

### Issue 6: ML Model Not Loaded

**Symptom:**
- Monitoring starts but ML detection not working
- Only rule-based detections (if any)

**Fix:**
1. Check if ML model exists:
```bash
ls -lh models/improved_ml_detector.joblib
ls -lh models/improved_ml_detector_metadata.json
```

2. If missing, train the model:
```bash
python train_improved.py
```

3. Restart application

---

## Complete Testing Procedure

### Pre-Test Checklist

- [ ] IDS/IPS application running as Administrator/root
- [ ] Network Monitor tab visible
- [ ] Monitoring started (Learning or Detection mode)
- [ ] Status shows "✓ Monitoring: ACTIVE"
- [ ] ML detector loaded (check logs)
- [ ] Correct network interface selected
- [ ] Firewall allows test traffic (or disabled temporarily)

### Test Procedure

**1. Start IDS/IPS:**
```bash
# As Administrator/root
cd IDS-IPS_AD
python src/main.py
```

**2. Start Monitoring:**
- Click Network Monitor tab
- Click "🚨 Start Detection Mode"
- Verify status: "✓ Monitoring: ACTIVE"

**3. Note Your IP:**
```bash
# On IDS/IPS PC
ipconfig  # Windows
ip addr   # Linux
# Example output: 192.168.1.50
```

**4. Update Threat Simulations:**
```python
# On attacking PC, edit threat_simulation_*.py:
TARGET_IP = "192.168.1.50"  # ← Your IDS/IPS PC's IP
```

**5. Run Port Scan:**
```bash
# From attacking PC
cd threat_simulations/
python threat_simulation_1_port_scan.py
```

**6. Check IDS/IPS:**
- Switch to Network Monitor tab
- Look at "Anomalies" table
- Check "Detection Log" area
- Verify statistics counters increased

**7. Run Brute Force:**
```bash
python threat_simulation_2_brute_force.py
```

**8. Run SYN Flood:**
```bash
# Requires admin/root
sudo python threat_simulation_3_syn_flood.py
```

**9. Review Detections:**
- All three attacks should be detected
- Each should show HIGH or CRITICAL severity
- ML confidence should be >80%

---

## Detection Flow

### How Detection Works

```
1. Threat Simulation (Attacking PC)
   ↓
2. Network Traffic (sent over network)
   ↓
3. Packet Capture (IDS/IPS PC - requires admin)
   ↓
4. Network Monitor (processes packets)
   ↓
5. Three-Layer Detection:
   a. Rule-Based Detection (port scan, brute force patterns)
   b. Baseline Anomaly Detection (unusual behavior)
   c. ML Detection (90.6% accuracy model)
   ↓
6. Alert Generation (if threat detected)
   ↓
7. UI Display (Network Monitor tab)
```

**CRITICAL:** If step 3 (Packet Capture) fails, NOTHING works!

---

## Validation Commands

### Check if Monitoring is Capturing Packets

**On IDS/IPS PC, check logs/console for:**
```
Processing packet: <src_ip> -> <dst_ip>
Flow analyzed: <details>
ML Result: <confidence>
```

**If you see these messages:** Packet capture is working ✓

**If you DON'T see these messages:** Packet capture is NOT working ✗

### Network Test (Before Threat Simulations)

**Simple connectivity test:**

**From attacking PC:**
```bash
# Ping IDS/IPS PC
ping 192.168.1.50

# Test port connectivity
telnet 192.168.1.50 22
nc 192.168.1.50 22
```

**On IDS/IPS PC (with monitoring active):**
- Should see connection attempts in logs
- Device count should increment
- Packet statistics should update

**If this simple test doesn't show up, threat simulations won't work either!**

---

## Quick Diagnosis

### Is Monitoring Actually Running?

**Check 1: Status Indicator**
- ✓ Monitoring: ACTIVE → Good!
- ⚠ Monitoring: Stopped → Not monitoring (click Start button)

**Check 2: Statistics**
- Packets count increasing → Capturing traffic ✓
- Devices count > 0 → Seeing devices ✓
- Packets count = 0 → NOT capturing traffic ✗

**Check 3: Console Output**
- Seeing "Processing packet..." → Working ✓
- No packet messages → NOT working ✗

---

## Summary

### The #1 Reason for No Detections:

**❌ Monitoring was never started!**

### The Fix:

1. ✅ Run as Administrator/root
2. ✅ Click "Network Monitor" tab
3. ✅ Click "🚨 Start Detection Mode"
4. ✅ Verify "✓ Monitoring: ACTIVE"
5. ✅ Run threat simulations
6. ✅ Watch detections appear!

---

## Expected Results (When Working Correctly)

**Console Output During Port Scan:**
```
[14:23:15] 🚨 ANOMALY DETECTED: Port Scan
   Source: 192.168.1.100
   Target: 192.168.1.50
   Severity: HIGH
   ML Confidence: 92.5%
   Rule Match: Rapid connection attempts (85 connections/min)
   Detection: Rule + ML Agreement
```

**UI Updates:**
- Anomalies table: New row added
- Statistics: Threats +1, Anomalies +1
- Detection log: Scrolling messages
- Visual indicators: Red highlights

**This should happen for EACH threat simulation!**

If you follow this guide and monitoring is properly started with administrator privileges, all three threat simulations should be detected! 🎯

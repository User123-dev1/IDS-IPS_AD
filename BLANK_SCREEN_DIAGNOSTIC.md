# Network Monitor Blank Screen - Diagnostic Guide

## Problem

You clicked "Start Detection Mode" in Network Monitor, then pinged the machine, but the screen remains blank with no detections or statistics showing.

---

## Issue #1: You're Pinging YOURSELF

**Your ping command:**
```
C:\Users\otlaptop>ping 192.168.12.190 -t
```

**The problem:** You're pinging 192.168.12.190 from the **SAME machine** (192.168.12.190). This traffic goes through the **loopback interface**, not the network interface, so packet capture **CANNOT see it**!

**Think of it like this:**
- Packet capture watches traffic going **in and out** of your network card
- When you ping yourself, the traffic never leaves your computer
- It's like trying to watch yourself walk out the door by looking out the window - you never actually leave!

---

## Solution #1: Ping from a DIFFERENT Computer

### From Another PC on the Same Network:

**From different PC:**
```bash
ping 192.168.12.190 -t
```

**On IDS/IPS PC (192.168.12.190):**
- Network Monitor should now show:
  - Packets count increasing
  - Device discovered (the PC you're pinging from)
  - Traffic statistics updating

---

## Issue #2: Packet Capture May Have Failed Silently

Even if you use a different PC, the screen might be blank because packet capture failed to start.

### Check the Console/Terminal

**Look at the PowerShell window where you ran `python src/main.py`**

**What you SHOULD see after clicking "Start Detection Mode":**
```
INFO:scanner.network_monitor:Starting network monitor (learning_mode=False)
INFO:scanner.secure_packet_capture:SecurePacketCapture initialized with safety limits
INFO:scanner.secure_packet_capture:Packet capture started (interface=Ethernet, filter=None)
```

**What indicates a PROBLEM:**
```
ERROR: Scapy error: ...
ERROR: Capture error: ...
ERROR: Permission denied
ERROR: No suitable interface found
WARNING: Monitoring already in progress
```

---

## Issue #3: Not Running as Administrator

**Symptom:** Monitoring appears to start but no packets are captured

**Check:**
```powershell
# In PowerShell, run:
[Security.Principal.WindowsIdentity]::GetCurrent().Groups -contains 'S-1-5-32-544'
```

**Should return:** `True`

**If returns:** `False` → You're NOT running as Administrator!

**Fix:**
1. Close the application
2. Right-click PowerShell → "Run as Administrator"
3. Navigate to project folder
4. Activate venv
5. Run: `python src/main.py`

---

## Issue #4: Npcap Not Installed or Not Working

**Check if Npcap is installed:**
```powershell
# Check if Npcap driver exists
Get-Service npcap

# Should show: Running
```

**If not found or not running:**
1. Download Npcap: https://npcap.com/#download
2. Install with **"WinPcap API-compatible Mode"** checked
3. Restart computer
4. Run application again

---

## Issue #5: Wrong Network Interface Selected

**Check your network interfaces:**
```powershell
ipconfig

# Look for the adapter with IP: 192.168.12.190
# Example output:
#   Ethernet adapter Ethernet:
#      IPv4 Address. . . . . . : 192.168.12.190
```

**Note the adapter name** (e.g., "Ethernet", "Wi-Fi", "Ethernet 2")

---

## Complete Diagnostic Procedure

### Step 1: Verify Administrator Privileges

```powershell
# Check if running as admin
whoami /groups | findstr "S-1-5-32-544"
```

**Should show:** `S-1-5-32-544`

**If not, restart as Administrator!**

### Step 2: Verify Npcap is Running

```powershell
Get-Service npcap
```

**Should show:** `Status: Running`

### Step 3: Start Network Monitor

1. Run: `python src/main.py`
2. Click " Network Monitor" tab
3. Click "🚨 Start Detection Mode"

### Step 4: Check Console Output

**Watch the PowerShell window for:**

**✅ GOOD - Monitoring Started:**
```
INFO:scanner.network_monitor:Starting network monitor (learning_mode=False)
INFO:scanner.secure_packet_capture:Packet capture started (interface=Ethernet, filter=None)
```

**❌ BAD - Error Messages:**
```
ERROR: Scapy error: ...
ERROR: Permission denied
WARNING: Monitoring already in progress
```

### Step 5: Verify UI Status

**In the Network Monitor tab, check:**
- Status indicator: Should show "🟢 DETECTION" (green)
- Duration timer: Should be counting up
- If status is gray or buttons are disabled, monitoring failed to start

### Step 6: Generate Network Traffic (FROM DIFFERENT PC!)

**CRITICAL: Use a DIFFERENT computer on the network!**

**From another PC on network (NOT the IDS/IPS machine):**
```bash
# Windows
ping 192.168.12.190 -t

# Linux/Mac
ping 192.168.12.190
```

**Or browse to the IDS/IPS machine:**
```
http://192.168.12.190
```

**Or try to connect to a port:**
```bash
telnet 192.168.12.190 80
```

### Step 7: Verify Data is Appearing

**After generating traffic from different PC, check Network Monitor:**

**Should see updates (within 1-2 seconds):**
- Packets count increasing (e.g., "Packets: 234")
- Devices count > 0 (e.g., "Devices: 2")
- Device table showing discovered devices
- Protocol statistics updating

**If still blank:**
- Check console for errors
- Verify you're using a DIFFERENT PC for traffic
- Try stopping and restarting monitoring

---

## Quick Test Script

**Run this from a DIFFERENT PC on the network:**

```python
# quick_test.py
import socket
import time

TARGET_IP = "192.168.12.190"  # Your IDS/IPS PC

print(f"Generating test traffic to {TARGET_IP}...")

for port in [80, 443, 22, 3389]:
    print(f"  Trying port {port}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((TARGET_IP, port))
        s.close()
        print(f"    ✓ Port {port} open")
    except:
        print(f"    ✗ Port {port} closed/filtered")
    time.sleep(0.5)

print("\nTest complete! Check IDS/IPS Network Monitor for detections.")
```

**Save as `quick_test.py` on different PC and run:**
```bash
python quick_test.py
```

**Expected on IDS/IPS:**
- Packets count increases by ~8-16
- Device appears in table (source of test traffic)
- Connection attempts show in statistics

---

## Common Mistakes

### ❌ Mistake 1: Self-Ping
```bash
# WRONG (from IDS/IPS machine):
ping 192.168.12.190

# This traffic is loopback - won't be captured!
```

**✅ Correct:**
```bash
# From DIFFERENT PC:
ping 192.168.12.190

# This traffic goes over network - will be captured!
```

### ❌ Mistake 2: Not Administrator
```
# Application looks like it's running but captures nothing
```

**✅ Correct:**
```powershell
# Right-click PowerShell → Run as Administrator
# Then run application
```

### ❌ Mistake 3: Firewall Blocking
```
# Firewall blocks incoming ping/traffic
# No packets reach network interface
```

**✅ Correct:**
```powershell
# Temporarily disable Windows Firewall for testing
# Or add firewall rule to allow ICMP (ping)
```

---

## Expected Behavior (When Working)

### After Starting Detection Mode:

**UI Should Show:**
- Status: "🟢 DETECTION" (green text)
- Duration: "Duration: 00:00:05" (counting up)
- Buttons: Start buttons disabled, Stop enabled

### After Traffic from Different PC:

**Within 1-2 seconds, should see:**
- Packets: "Packets: 15" (and increasing)
- Devices: "Devices: 2" (or more)
- Devices table: Shows IP of source machine
- Protocol table: Shows protocols used (ICMP, TCP, etc.)

### If Attack Detected:

**Anomalies table should show:**
- Timestamp
- Severity (HIGH, CRITICAL, etc.)
- Category (PORT_SCAN, BRUTE_FORCE, etc.)
- Description
- Source IP

---

## Troubleshooting Checklist

Before running threat simulations, verify ALL of these:

- [ ] Running as **Administrator** (verified with `whoami /groups`)
- [ ] Npcap **installed and running** (`Get-Service npcap`)
- [ ] **" Network Monitor"** tab selected (NOT "ML Detection")
- [ ] Clicked **"🚨 Start Detection Mode"** button
- [ ] Status shows **"🟢 DETECTION"** (green)
- [ ] Console shows **"Packet capture started"**
- [ ] **NO error messages** in console
- [ ] Network interface is **active** (`ipconfig` shows IP)
- [ ] Testing from **DIFFERENT PC** (NOT self-ping!)
- [ ] Firewall **allows incoming** traffic (or temporarily disabled)
- [ ] Packets count **increases** when traffic sent from different PC

**If ANY of these fail, fix that issue first before proceeding!**

---

## Getting Console Output

**To see detailed debug output:**

1. Close application
2. Edit `src/scanner/network_monitor.py`
3. At top, change:
```python
logging.basicConfig(level=logging.INFO)
```
to:
```python
logging.basicConfig(level=logging.DEBUG)
```

4. Restart application
5. Watch console for detailed messages about packet capture

---

## Still Not Working?

### Collect Diagnostic Information:

**1. Check Scapy Installation:**
```python
python
>>> import scapy
>>> from scapy.all import sniff
>>> # Should not error
```

**2. Manual Packet Capture Test:**
```python
from scapy.all import sniff

def packet_callback(packet):
    print(f"Got packet: {packet.summary()}")

# This requires Administrator privileges
sniff(prn=packet_callback, count=10)
```

**If this works:** Problem is in our code integration
**If this fails:** Problem is with Scapy/Npcap setup

**3. Check Interface List:**
```python
from scapy.all import get_if_list
print(get_if_list())
```

Should show your network interfaces.

---

## Summary

**Your immediate issue:** You're pinging yourself (192.168.12.190 → 192.168.12.190)

**The fix:**
1. Use a **DIFFERENT computer** to ping/attack the IDS/IPS machine
2. Verify you're running as **Administrator**
3. Check console for **error messages**
4. Verify **Npcap is installed and running**
5. Make sure **status shows green "🟢 DETECTION"**

**Test command (from DIFFERENT PC):**
```bash
ping 192.168.12.190 -t
```

**Expected result:**
- Packets count increases
- Device appears in table
- Statistics update

**Then try threat simulations (from different PC):**
```bash
cd threat_simulations/
python threat_simulation_1_port_scan.py
```

This should trigger detections! 🎯

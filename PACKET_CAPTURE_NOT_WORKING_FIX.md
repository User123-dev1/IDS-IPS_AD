# CRITICAL: Packet Capture Not Working - Complete Fix Guide

## Problem

You're pinging the IDS/IPS PC from another computer and the ping succeeds, BUT the application shows:
- ❌ No packet count increasing
- ❌ No devices being discovered
- ❌ No statistics updating
- ❌ Screen remains blank/empty

**This means packet capture is COMPLETELY failing!**

---

## Root Cause Analysis

When packet capture fails completely (zero packets), it's usually one of these:

1. **Not running as Administrator** (most common)
2. **Npcap not installed or not working**
3. **Wrong network interface selected**
4. **Npcap service not running**
5. **Firewall blocking packet capture**
6. **Application didn't actually start monitoring**

---

## Step-by-Step Diagnosis and Fix

### Step 1: Run the Diagnostic Tool

I've created a diagnostic tool to test packet capture.

**Run as Administrator:**
```powershell
# Right-click PowerShell → Run as Administrator
cd C:\Users\otlaptop\PycharmProjects\IDS-IPS_AD

# Make sure virtual environment is activated
.venv\Scripts\activate

# Run diagnostic
python test_packet_capture.py
```

**What it does:**
1. ✓ Checks Administrator privileges
2. ✓ Checks Scapy installation
3. ✓ Checks Npcap service status
4. ✓ Lists network interfaces
5. ✓ **Tests actual packet capture for 10 seconds**

**During the test:**
- From another PC, ping the IDS/IPS PC
- Watch the diagnostic tool output
- Should see packets like: `[1] ICMP (ping): 192.168.12.190 → 192.168.12.193`

**If you see packets → Packet capture works!**
**If you see NO packets → Packet capture is broken!**

---

### Step 2: Verify You're Running as Administrator

**Check in PowerShell:**
```powershell
# This should return S-1-5-32-544
whoami /groups | findstr "S-1-5-32-544"
```

**If nothing returned:**
- You're NOT running as Administrator!
- Close everything
- Right-click PowerShell → "Run as Administrator"
- Try again

---

### Step 3: Check Npcap Service

**Verify Npcap is running:**
```powershell
Get-Service npcap
```

**Should show:**
```
Status   Name       DisplayName
------   ----       -----------
Running  npcap      Npcap Packet Driver (NPCAP)
```

**If Status is "Stopped":**
```powershell
Start-Service npcap
```

**If service doesn't exist:**
- Npcap not installed!
- Download: https://npcap.com/#download
- Install as Administrator
- **Check "Install Npcap in WinPcap API-compatible Mode"**
- **Restart computer**

---

### Step 4: Verify Correct Network Interface

**List your network adapters:**
```powershell
ipconfig

# Look for the adapter with IP 192.168.12.193
# Example output:
#   Ethernet adapter Ethernet:
#      IPv4 Address. . . . . . : 192.168.12.193
```

**Note the adapter name** (e.g., "Ethernet", "Wi-Fi", "Ethernet 2")

**Check Scapy sees this interface:**
```python
python -c "from scapy.all import get_if_list; print('\n'.join(get_if_list()))"
```

**Should show a list of interfaces.**

---

### Step 5: Test Basic Packet Capture

**Run this simple test:**

```python
# test_capture_simple.py
from scapy.all import sniff, IP

print("Starting packet capture test...")
print("Ping this PC from another computer NOW!")
print("Waiting 10 seconds...\n")

counter = [0]

def packet_handler(pkt):
    counter[0] += 1
    if pkt.haslayer(IP):
        print(f"Packet {counter[0]}: {pkt[IP].src} → {pkt[IP].dst}")

sniff(prn=packet_handler, timeout=10, store=False)

print(f"\nCaptured {counter[0]} packets")
if counter[0] > 0:
    print("✓ Packet capture WORKS!")
else:
    print("✗ Packet capture FAILED!")
```

**Save this and run as Administrator:**
```powershell
python test_capture_simple.py
```

**While it runs, ping from another PC:**
```bash
ping 192.168.12.193
```

**If you see packets → Scapy works!**
**If NO packets → Npcap/Scapy broken!**

---

### Step 6: Check Application Console

**When you start the IDS/IPS application, watch the console for:**

**Good messages (capture working):**
```
INFO:scanner.network_monitor:Starting network monitor (learning_mode=False)
INFO:scanner.secure_packet_capture:SecurePacketCapture initialized
INFO:scanner.secure_packet_capture:Packet capture started (interface=Ethernet, filter=None)
```

**Bad messages (capture failing):**
```
ERROR: Scapy error: ...
ERROR: Permission denied
ERROR: No suitable interface found
WARNING: Monitoring already in progress
```

**If you see errors:**
- Note the exact error message
- This tells you what's wrong

**If you see NOTHING:**
- Packet capture might have failed silently
- Check if monitor actually started

---

### Step 7: Verify Monitoring Actually Started

**In the application:**

1. Check the **Status indicator** in Network Monitor tab
   - Should show: **"🟢 DETECTION"** (green) or **"🟢 LEARNING"**
   - If gray or says "Stopped" → Not monitoring!

2. Check the **buttons**:
   - "Start Learning" and "Start Detection" should be **disabled** (grayed out)
   - "Stop" button should be **enabled**
   - If backwards → Not monitoring!

3. Check **Duration timer**:
   - Should be counting up: "Duration: 00:00:05, 00:00:06..."
   - If stuck at 00:00:00 → Not monitoring!

**If monitoring didn't start:**
- Close application
- Check console for error messages
- Restart as Administrator
- Try clicking "Start Detection Mode" again

---

## Common Issues and Fixes

### Issue 1: "Access Denied" or "Permission Denied"

**Cause:** Not running as Administrator

**Fix:**
1. Close application
2. Right-click PowerShell → "Run as Administrator"
3. Activate virtual environment
4. Run application again

### Issue 2: "Npcap is not installed"

**Cause:** Npcap missing or not working

**Fix:**
1. Download Npcap: https://npcap.com/#download
2. **Close ALL applications** (including IDS/IPS)
3. Run Npcap installer **as Administrator**
4. **Check "Install Npcap in WinPcap API-compatible Mode"**
5. Complete installation
6. **Restart computer** (important!)
7. Verify: `Get-Service npcap` shows "Running"

### Issue 3: Npcap Service Not Running

**Fix:**
```powershell
# Start service
Start-Service npcap

# Set to auto-start
Set-Service npcap -StartupType Automatic
```

### Issue 4: Wrong Network Interface

**Symptoms:**
- Packet capture seems to start
- But no packets captured
- `Get-Service npcap` shows Running

**Cause:** Scapy selected wrong interface (e.g., loopback, VPN, disconnected adapter)

**Fix:** Need to specify interface explicitly

**Find correct interface:**
```powershell
# Show interfaces with IPs
ipconfig /all

# Note the name of adapter with IP 192.168.12.193
```

**Modify code to use specific interface:**
Edit `src/gui/live_dashboard.py` line 763:
```python
# Before:
success = self.monitor.start_monitoring(learn_baseline=learn)

# After (specify your interface):
success = self.monitor.start_monitoring(
    interface="Ethernet",  # ← Change to your adapter name
    learn_baseline=learn
)
```

### Issue 5: Windows Firewall Blocking

**Check if firewall is blocking:**
```powershell
# Temporarily disable Windows Firewall (for testing only)
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False

# Run test

# Re-enable after test
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
```

**If this fixes it:**
- Firewall is blocking
- Add firewall rule to allow Python/packet capture

### Issue 6: Application Shows Green Status But No Packets

**Symptoms:**
- Status shows "🟢 DETECTION"
- Duration counting up
- But Packets stays at 0

**Possible causes:**
- Wrong interface selected
- Packet capture thread crashed silently
- No traffic on selected interface

**Debug steps:**

1. Check console for errors after clicking Start
2. Run diagnostic: `python test_packet_capture.py`
3. If diagnostic captures packets but app doesn't → Application bug
4. If diagnostic also fails → System-level issue

---

## The Nuclear Option: Complete Reinstall

If nothing works, do a complete clean reinstall:

```powershell
# 1. Uninstall Npcap
# Control Panel → Programs → Uninstall Npcap

# 2. Restart computer

# 3. Reinstall Npcap
# Download from https://npcap.com/
# Run as Administrator
# Check "WinPcap API-compatible Mode"
# Restart computer

# 4. Reinstall Scapy
pip uninstall scapy
pip install scapy

# 5. Test
python test_packet_capture.py
```

---

## Verification Checklist

Before running the IDS/IPS application, verify ALL of these:

- [ ] Running PowerShell **as Administrator** (`whoami /groups` contains S-1-5-32-544)
- [ ] Npcap service **Running** (`Get-Service npcap`)
- [ ] Virtual environment **activated** (see (.venv) in prompt)
- [ ] Diagnostic test **captures packets** (`python test_packet_capture.py`)
- [ ] Simple test **captures packets** (`python test_capture_simple.py`)
- [ ] Network adapter has **correct IP** (`ipconfig`)
- [ ] No VPN or **virtual adapters** interfering
- [ ] Windows Firewall **allows** packet capture (or disabled for test)
- [ ] Application shows **"🟢 DETECTION"** after clicking Start
- [ ] Console shows **"Packet capture started"**
- [ ] Duration timer **counting up**
- [ ] Testing from **different PC** (not self-ping)

**If ALL checkboxes are checked and still no packets:**
- Provide console error messages for further diagnosis
- Check if using correct Network Monitor tab (not legacy ML Detection tab)

---

## Expected Behavior (When Working)

**After clicking "Start Detection Mode":**

**Within 1-2 seconds:**
- Status: "🟢 DETECTION" (green)
- Duration: "Duration: 00:00:01" (counting up)
- Console: "Packet capture started (interface=Ethernet, filter=None)"

**After ping from different PC:**
- Packets: "Packets: 4" (increases with each ping)
- Devices: "Devices: 2" (pinging PC appears)
- Protocol table: Shows "ICMP" protocol
- Devices table: Shows source IP address

**If port scan from different PC:**
- Packets: Increases significantly (hundreds)
- Anomalies: "Anomalies: 1"
- Anomalies table: Shows PORT_SCAN alert
- Severity: HIGH or CRITICAL

---

## Still Not Working?

**Provide this information for further help:**

1. **Diagnostic test output:**
   ```
   python test_packet_capture.py
   [paste full output]
   ```

2. **Npcap service status:**
   ```
   Get-Service npcap
   [paste output]
   ```

3. **Administrator check:**
   ```
   whoami /groups | findstr S-1-5-32-544
   [paste output]
   ```

4. **Console error messages:**
   ```
   [paste any ERROR or WARNING messages from console]
   ```

5. **Network adapters:**
   ```
   ipconfig /all
   [paste output]
   ```

6. **Scapy interfaces:**
   ```
   python -c "from scapy.all import get_if_list; print('\n'.join(get_if_list()))"
   [paste output]
   ```

---

## Summary

**Zero packets = Packet capture completely broken**

**Most common cause:** Not running as Administrator

**Quick fix attempt:**
1. Close everything
2. Right-click PowerShell → "Run as Administrator"
3. Run: `python test_packet_capture.py`
4. Ping during test from different PC
5. If packets captured → Run IDS/IPS app
6. If no packets → Reinstall Npcap and restart computer

**The diagnostic tool (`test_packet_capture.py`) will tell you exactly what's wrong!** 🎯

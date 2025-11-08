# IDS/IPS Troubleshooting Index

Quick navigation to the right troubleshooting guide for your issue.

---

## 🚀 First Time Setup

**Starting fresh on a new PC?**
→ Read: **[NEW_PC_SETUP_GUIDE.md](NEW_PC_SETUP_GUIDE.md)**

**Want the quickest way to get started?**
→ Read: **[QUICK_START.md](QUICK_START.md)**

---

## 🔍 Choose Your Issue

### Issue 1: Application Won't Start / Reference Errors

**Symptoms:**
- Application crashes on startup
- Error messages about missing modules (PyQt6, pandas, scapy, etc.)
- "No module named..." errors
- Import errors in console

**Solution:**
→ **[NEW_PC_SETUP_GUIDE.md](NEW_PC_SETUP_GUIDE.md)**

**Quick Fix:**
```powershell
# Run as Administrator
.\RUN_AS_ADMIN.bat
```

---

### Issue 2: Red Underlines in IDE (PyCharm/VS Code)

**Symptoms:**
- Red underlines on import statements in your IDE
- Warnings about unresolved references
- Code looks broken in IDE but runs fine

**Solution:**
→ **[IDE_IMPORT_WARNINGS_FIX.md](IDE_IMPORT_WARNINGS_FIX.md)**

**Note:** These are just IDE warnings - the code runs fine!

---

### Issue 3: All 255 IPs Showing as Devices

**Symptoms:**
- Network scan shows all 255 IP addresses
- Topology graph cluttered with offline devices
- Device table shows unreachable devices
- Only want to see active/online devices

**Solution:**
→ **[ACTIVE_DEVICE_FILTERING_FIX.md](ACTIVE_DEVICE_FILTERING_FIX.md)**

---

### Issue 4: No Threat Detections

**Symptoms:**
- Running threat simulations (port scans, pings, etc.)
- But nothing appears in anomalies/alerts
- ML detector not finding anything
- Network Monitor shows no threats

**Solution:**
→ **[WRONG_MONITORING_SYSTEM_FIX.md](WRONG_MONITORING_SYSTEM_FIX.md)**

**Key Check:** Look at console logs:
- ❌ If you see "Scan interval: 30 seconds" → You're using the WRONG (legacy) system
- ✅ If you see "Packet capture started" → You're using the RIGHT system

---

### Issue 5: Blank Screen After Starting Monitoring

**Symptoms:**
- Clicked "Start Detection Mode" or "Start Learning"
- Status shows green and "DETECTION" or "LEARNING"
- Duration timer counting up
- But screen remains blank - no packets, no devices, no stats
- Testing from same PC (self-ping)

**Solution:**
→ **[BLANK_SCREEN_DIAGNOSTIC.md](BLANK_SCREEN_DIAGNOSTIC.md)**

**Quick Check:** Are you pinging from a DIFFERENT PC?
- ❌ Self-ping (same PC) → Uses loopback, won't show in capture
- ✅ Different PC → Network traffic, will be captured

---

### Issue 6: ZERO Packets Captured (CRITICAL)

**Symptoms:**
- Pinging from different PC successfully
- But IDS/IPS shows: Packets: 0, Devices: 0
- Everything stays at zero
- No statistics updating at all
- Packet capture completely failing

**Solution:**
→ **[PACKET_CAPTURE_NOT_WORKING_FIX.md](PACKET_CAPTURE_NOT_WORKING_FIX.md)**

**Emergency Diagnostic:**
```powershell
# Run as Administrator
python test_packet_capture.py
```

**Most Common Cause:** Not running as Administrator!

---

## 🛠️ Diagnostic Tools

### Quick Test Scripts

**1. Full Diagnostic (Recommended)**
```powershell
# Checks everything: Admin, Npcap, interfaces, packet capture
python test_packet_capture.py
```

**2. Simple Packet Capture Test**
```powershell
# Quick test if Scapy can capture packets
python test_capture_simple.py
```

**3. Threat Simulation Tests**
```powershell
# From DIFFERENT PC, run these to generate test traffic:
python threat_simulation/port_scan.py <target_ip>
python threat_simulation/dos_simulation.py <target_ip>
python threat_simulation/arp_scan.py <target_ip>
```

---

## 📋 Common Commands

### Check Administrator Privileges
```powershell
whoami /groups | findstr "S-1-5-32-544"
# If output shown → Running as Admin ✓
# If nothing shown → NOT Admin ✗
```

### Check Npcap Service
```powershell
Get-Service npcap
# Should show: Status = Running
```

### Start Npcap Service
```powershell
Start-Service npcap
```

### Check Python Packages
```powershell
pip list | findstr -i "pyqt6 scapy pandas numpy scikit"
```

### Install Dependencies
```powershell
pip install PyQt6 scapy pandas numpy scikit-learn joblib matplotlib pyqtgraph requests psutil
```

---

## 🎯 Quick Troubleshooting Decision Tree

```
Start Here
    │
    ├─ App won't start / crashes?
    │   └─> NEW_PC_SETUP_GUIDE.md
    │
    ├─ Red underlines in IDE?
    │   └─> IDE_IMPORT_WARNINGS_FIX.md (or just ignore them)
    │
    ├─ Shows all 255 devices?
    │   └─> ACTIVE_DEVICE_FILTERING_FIX.md
    │
    ├─ No threat detections?
    │   └─> WRONG_MONITORING_SYSTEM_FIX.md
    │
    ├─ Screen blank after starting?
    │   │
    │   ├─ Testing from same PC?
    │   │   └─> BLANK_SCREEN_DIAGNOSTIC.md
    │   │
    │   └─ Testing from different PC?
    │       └─> PACKET_CAPTURE_NOT_WORKING_FIX.md
    │
    └─ Zero packets captured?
        └─> PACKET_CAPTURE_NOT_WORKING_FIX.md
            └─> Run: python test_packet_capture.py
```

---

## 📚 All Documentation Files

### Setup Guides
- **[QUICK_START.md](QUICK_START.md)** - Fast reference for common tasks
- **[NEW_PC_SETUP_GUIDE.md](NEW_PC_SETUP_GUIDE.md)** - Complete setup on new PC
- **[requirements.txt](requirements.txt)** - Python dependencies

### Troubleshooting Guides
- **[PACKET_CAPTURE_NOT_WORKING_FIX.md](PACKET_CAPTURE_NOT_WORKING_FIX.md)** - Zero packets captured
- **[BLANK_SCREEN_DIAGNOSTIC.md](BLANK_SCREEN_DIAGNOSTIC.md)** - Screen blank after start
- **[WRONG_MONITORING_SYSTEM_FIX.md](WRONG_MONITORING_SYSTEM_FIX.md)** - No detections
- **[ACTIVE_DEVICE_FILTERING_FIX.md](ACTIVE_DEVICE_FILTERING_FIX.md)** - All IPs showing
- **[IDE_IMPORT_WARNINGS_FIX.md](IDE_IMPORT_WARNINGS_FIX.md)** - Red underlines in IDE

### Launcher Scripts
- **[RUN_AS_ADMIN.bat](RUN_AS_ADMIN.bat)** - Double-click launcher
- **[run_app.ps1](run_app.ps1)** - Automated setup script

### Diagnostic Tools
- **[test_packet_capture.py](test_packet_capture.py)** - Full diagnostic test
- **[test_capture_simple.py](test_capture_simple.py)** - Simple capture test

---

## 💡 Pro Tips

1. **Always run as Administrator** for packet capture
2. **Use different PC** for testing (not self-ping)
3. **Check the console logs** for error messages
4. **Run diagnostic tools** before asking for help
5. **Use Network Monitor tab**, not legacy ML Detection tab

---

## 🆘 Still Need Help?

If none of the guides solve your issue:

1. Run the diagnostic tool:
   ```powershell
   python test_packet_capture.py
   ```

2. Gather this information:
   - Diagnostic tool output
   - Console error messages
   - Output of: `Get-Service npcap`
   - Output of: `whoami /groups | findstr S-1-5-32-544`

3. Check which monitoring system you're using:
   - Look at console logs when you start monitoring
   - "Scan interval: 30 seconds" = Wrong system
   - "Packet capture started" = Right system

---

## ✅ Expected Working Behavior

When everything is working correctly:

**After clicking "Start Detection Mode":**
1. Console shows: "Packet capture started (interface=Ethernet, filter=None)"
2. Status shows: "🟢 DETECTION" (green)
3. Duration counts up: "Duration: 00:00:01, 00:00:02..."

**After ping from different PC:**
4. Packets counter increases: "Packets: 4, 8, 12..."
5. Devices counter increases: "Devices: 2"
6. Protocol table shows: ICMP packets
7. Devices table shows: Source IP address

**After port scan from different PC:**
8. Packets increase significantly (hundreds)
9. Anomalies counter increases: "Anomalies: 1"
10. Anomalies table shows: PORT_SCAN alert
11. Severity shows: HIGH or CRITICAL

---

**Last Updated:** 2025-11-08

# IDS/IPS Quick Start Guide

## ⚡ Fastest Way to Run (3 Steps)

### Method 1: Double-Click Launcher (Easiest!)

1. **Right-click** `RUN_AS_ADMIN.bat`
2. Select **"Run as administrator"**
3. Done! Application will start automatically

The launcher script will:
- ✓ Check all requirements
- ✓ Create virtual environment if needed
- ✓ Install missing packages automatically
- ✓ Verify ML model exists
- ✓ Start the application

---

### Method 2: PowerShell Script

1. **Right-click PowerShell → "Run as Administrator"**
2. Navigate to project folder:
   ```powershell
   cd C:\Users\<YourUsername>\PycharmProjects\IDS-IPS_AD
   ```
3. Run the launcher:
   ```powershell
   .\run_app.ps1
   ```

---

### Method 3: Manual Run

```powershell
# As Administrator
cd C:\Users\<YourUsername>\PycharmProjects\IDS-IPS_AD

# Activate virtual environment
.venv\Scripts\activate

# Run application
python src\main.py
```

---

## 🔴 Red Underlines in IDE? (They're Just Warnings!)

If you see red underlines on imports like:
```python
from gui.rule_manager_window import RuleManagerWindow
```

**Don't worry!** The code **WILL RUN FINE**. These are just IDE warnings.

### Quick Fix for PyCharm:
1. Right-click `src` folder
2. **"Mark Directory as"** → **"Sources Root"**
3. Red underlines disappear!

### Quick Fix for VS Code:
Create `.vscode/settings.json`:
```json
{
    "python.analysis.extraPaths": ["./src"]
}
```

**Full guide:** See `IDE_IMPORT_WARNINGS_FIX.md`

---

## ✅ First-Time Setup Checklist

**Required (once):**
- [ ] Python 3.10+ installed
- [ ] Npcap installed from https://npcap.com/
- [ ] Virtual environment created: `python -m venv .venv`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] ML model files in `models/` folder

**Every time you run:**
- [ ] Run as **Administrator** (required for packet capture)
- [ ] Virtual environment activated
- [ ] Launch from project root folder

---

## 🚀 Using the Application

### Step 1: Start Network Monitoring

1. Click **" Network Monitor"** tab
2. Click **"🚨 Start Detection Mode"** button
3. Wait for status: **"🟢 DETECTION"**

**Console should show:**
```
INFO:scanner.network_monitor:Starting network monitor
INFO:scanner.secure_packet_capture:Packet capture started
```

### Step 2: Test Detection

**From a DIFFERENT PC on the network:**

```bash
# Ping test
ping <YOUR_IDS_PC_IP> -t

# Port scan test
cd threat_simulations/
python threat_simulation_1_port_scan.py
```

**On IDS/IPS PC, you should see:**
- Packets count increasing
- Devices appearing in table
- Threat alerts for port scan

---

## 🔧 Common Issues

### Issue 1: "No module named 'PyQt6'"

**Fix:**
```powershell
.venv\Scripts\activate
pip install PyQt6 scapy pandas numpy scikit-learn joblib
```

### Issue 2: Blank Screen / No Detections

**Causes:**
1. Not running as Administrator
2. Npcap not installed
3. Testing from same PC (use different PC!)
4. Monitoring not started

**Fix:**
- Run as Administrator
- Install Npcap: https://npcap.com/
- Test from DIFFERENT computer
- Click "Start Detection Mode" button

### Issue 3: "Permission Denied"

**Fix:** Run PowerShell as Administrator

### Issue 4: Red Underlines in IDE

**Fix:** Mark `src` as Sources Root (PyCharm) or see `IDE_IMPORT_WARNINGS_FIX.md`

---

## 📖 Documentation Index

**Setup Guides:**
- `NEW_PC_SETUP_GUIDE.md` - Complete setup for new PC
- `QUICK_START.md` - This file
- `requirements.txt` - Python dependencies

**Troubleshooting:**
- `IDE_IMPORT_WARNINGS_FIX.md` - Fix red underlines in IDE
- `BLANK_SCREEN_DIAGNOSTIC.md` - Fix blank network monitor
- `WRONG_MONITORING_SYSTEM_FIX.md` - Legacy vs real-time system
- `THREAT_DETECTION_TROUBLESHOOTING.md` - Detection issues

**Feature Documentation:**
- `ALERT_RULES_ML_INTEGRATION.md` - Alert rules + ML integration
- `ML_INTEGRATION_GUIDE.md` - ML detector usage
- `MODEL_TRAINING_SUCCESS.md` - Model training info
- `ACTIVE_DEVICE_FILTERING_FIX.md` - Active device filtering

**Testing:**
- `threat_simulations/` - Threat simulation scripts
- `threat_simulations/README.md` - How to use simulations

---

## 💡 Quick Tips

### Tip 1: Use the Launcher!
**Don't manually run the application.** Use `RUN_AS_ADMIN.bat` - it handles everything!

### Tip 2: Different PC for Testing
**Always test from a DIFFERENT computer on the network.** Self-ping won't work!

### Tip 3: Check Console
**Watch the PowerShell window for errors.** Most issues show helpful error messages.

### Tip 4: Ignore IDE Warnings
**Red underlines in IDE are cosmetic.** The code runs fine! Configure your IDE if they bother you.

### Tip 5: Verify Packet Capture
**After starting monitoring, watch the console.** You should see packet processing messages.

---

## 🎯 Success Checklist

**Application is working correctly when:**
- [ ] Launches without import errors
- [ ] Network Monitor tab visible
- [ ] Status shows "🟢 DETECTION" after clicking Start
- [ ] Console shows "Packet capture started"
- [ ] Packets count increases when traffic from different PC
- [ ] Devices appear in devices table
- [ ] Port scan from different PC triggers HIGH severity alert

---

## 📞 Still Having Issues?

**Check these in order:**

1. **Read the error message** - Most errors tell you exactly what's wrong
2. **Check console output** - Look for ERROR or WARNING messages
3. **Verify Administrator** - Run: `whoami /groups | findstr S-1-5-32-544`
4. **Check Npcap** - Run: `Get-Service npcap`
5. **Verify dependencies** - Run: `pip list | findstr PyQt6`
6. **Test from different PC** - Don't ping yourself!
7. **Read relevant guide** - Check documentation index above

---

## ⚡ TL;DR (Too Long; Didn't Read)

**Super Quick Start:**
1. Pull latest code: `git pull`
2. Right-click `RUN_AS_ADMIN.bat` → "Run as administrator"
3. Click " Network Monitor" tab
4. Click "🚨 Start Detection Mode"
5. Test from DIFFERENT PC: `python threat_simulation_1_port_scan.py`
6. Watch detections appear!

**Red underlines in IDE?**
- They're just warnings
- Code runs fine
- Fix: Mark `src` as Sources Root

**Blank screen?**
- Test from DIFFERENT PC (not self-ping!)
- Check console for errors
- Verify running as Administrator

That's it! 🚀

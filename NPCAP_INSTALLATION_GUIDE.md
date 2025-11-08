# Npcap Installation Guide

## What is Npcap?

Npcap is a Windows packet capture library required for the IDS/IPS application to monitor network traffic. **Without Npcap, packet capture will not work.**

---

## Step-by-Step Installation

### Step 1: Download Npcap

1. Go to: **https://npcap.com/**
2. Click **"Download"**
3. Download the latest installer (usually `npcap-X.XX.exe`)

**Direct link:** https://npcap.com/#download

---

### Step 2: Run Installer as Administrator

1. **Right-click** the downloaded `npcap-X.XX.exe`
2. Select **"Run as administrator"**
3. Click **"Yes"** when Windows asks for permission

---

### Step 3: Configure Installation Options

**IMPORTANT - Check these options:**

1. ✓ **"WinPcap API-compatible Mode"** - **MUST be checked!**
   - This allows Scapy to work with Npcap
   - Without this, packet capture will fail

2. ✓ **"Support raw 802.11 traffic"** - Optional but recommended
   - Enables wireless packet capture

3. ✓ **"Restrict Npcap driver's access to Administrators only"** - Recommended for security

**Screenshot of what to check:**
```
[X] WinPcap API-compatible Mode  <-- CRITICAL!
[X] Support raw 802.11 traffic
[X] Restrict Npcap driver's access to Administrators only
```

4. Click **"Install"**

---

### Step 4: Restart Computer

**After installation completes:**

1. Click **"Finish"**
2. **Restart your computer** (required!)
   - Npcap driver loads during boot
   - Services won't work until after restart

---

## Verify Installation

After restart, verify Npcap is installed and running:

### Method 1: Check Service Status (PowerShell)

```powershell
# Open PowerShell as Administrator
Get-Service npcap
```

**Expected output:**
```
Status   Name               DisplayName
------   ----               -----------
Running  npcap              Npcap Packet Driver (NPCAP)
```

If status is **"Running"** --> Npcap is working! ✓

---

### Method 2: Run Diagnostic Tool

```powershell
# In your project folder
python test_packet_capture.py
```

**Expected output:**
```
[3] Checking Npcap service...
    [OK] Npcap service is running
```

---

## Troubleshooting

### Issue 1: "Service does not exist" (Error 1060)

**Problem:** Npcap not installed

**Fix:**
1. Download from https://npcap.com/
2. Run installer as Administrator
3. **CHECK "WinPcap API-compatible Mode"**
4. Restart computer

---

### Issue 2: Service is "Stopped"

**Fix:**
```powershell
# Run as Administrator
Start-Service npcap
```

Then check again:
```powershell
Get-Service npcap
```

---

### Issue 3: "Could not start the pcap service"

**Causes:**
1. Not running PowerShell as Administrator
2. Npcap driver not loaded (restart required)
3. Installation incomplete

**Fix:**
1. Restart computer
2. Run PowerShell as Administrator
3. Try starting service manually: `Start-Service npcap`
4. If still fails, reinstall Npcap

---

### Issue 4: WinPcap Conflict

**Error:** "WinPcap is now deprecated"

**Fix:**
1. Uninstall old WinPcap:
   - Settings -> Apps -> WinPcap -> Uninstall
2. Install Npcap (follow steps above)
3. Restart computer

---

## Complete Installation Checklist

Before running the IDS/IPS application:

- [ ] Downloaded Npcap from https://npcap.com/
- [ ] Ran installer as Administrator
- [ ] **Checked "WinPcap API-compatible Mode"** (CRITICAL!)
- [ ] Installation completed successfully
- [ ] **Restarted computer**
- [ ] Verified service: `Get-Service npcap` shows "Running"
- [ ] Tested with: `python test_packet_capture.py`

---

## After Installation

Once Npcap is installed and running:

1. **Run IDS/IPS as Administrator:**
   ```powershell
   # Right-click PowerShell -> "Run as administrator"
   cd C:\Users\<YourUsername>\PycharmProjects\IDS-IPS_AD
   .venv\Scripts\activate
   python src\main.py
   ```

2. **Or use the launcher:**
   - Right-click `RUN_AS_ADMIN.bat` -> "Run as administrator"

3. **Verify packet capture works:**
   - Click "Network Monitor" tab
   - Click "Start Detection Mode"
   - Ping from another PC
   - You should see packets counting up!

---

## Still Not Working?

If Npcap is installed and running but packet capture still fails:

1. **Run full diagnostic:**
   ```powershell
   python test_packet_capture.py
   ```

2. **Check firewall:**
   - Windows Firewall may block packet capture
   - Temporarily disable to test

3. **Verify network interface:**
   - Make sure you're on the correct network adapter
   - Wireless vs Ethernet

4. **See troubleshooting guides:**
   - `PACKET_CAPTURE_NOT_WORKING_FIX.md` - Complete troubleshooting
   - `TROUBLESHOOTING_INDEX.md` - All guides index

---

## Important Notes

**Security:**
- Npcap requires Administrator privileges for packet capture
- Always run IDS/IPS as Administrator
- Restricting Npcap access to Administrators is recommended

**Compatibility:**
- Npcap replaces the deprecated WinPcap
- Uninstall WinPcap before installing Npcap
- "WinPcap API-compatible Mode" ensures Scapy compatibility

**Performance:**
- Npcap is more efficient than WinPcap
- Supports modern Windows versions (Windows 10/11)
- Better performance on high-speed networks

---

## Quick Reference

**Download:** https://npcap.com/

**Check status:**
```powershell
Get-Service npcap
```

**Start service:**
```powershell
Start-Service npcap
```

**Test packet capture:**
```powershell
python test_packet_capture.py
```

---

**Last Updated:** 2025-11-08

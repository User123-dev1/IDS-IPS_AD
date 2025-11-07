# Threat Simulation Quick Start Guide

## 5-Minute Setup and Testing

This guide will help you quickly test your IDS/IPS system with simulated attacks.

---

## Setup (2 minutes)

### On IDS/IPS Computer (192.168.1.10)

```bash
# 1. Start the IDS/IPS application
cd C:\Users\otlaptop\PycharmProjects\IDS-IPS_AD
python src/main.py

# 2. In the GUI:
#    - Click on "Network Monitor" tab
#    - Click "Start Monitoring" button
#    - Verify: Status shows "Monitoring Active"
```

### On Attacker Computer (192.168.1.100)

```bash
# 1. Download threat simulation scripts
git clone <repo> or copy threat_simulations folder

# 2. Edit TARGET_IP in scripts
#    Change "192.168.1.50" to your IDS/IPS IP (192.168.1.10)
```

---

## Quick Tests (3 minutes)

### Test 1: Port Scan (30 seconds)

**Python:**
```bash
python threat_simulation_1_port_scan.py
```

**PowerShell:**
```powershell
.\ThreatSimulation-PortScan.ps1
```

**Expected Detection:**
- ✅ Alert in "Network Monitor" within 10 seconds
- ✅ Category: PORT_SCAN
- ✅ Severity: CRITICAL
- ✅ Threat Level: HIGH or CRITICAL

---

### Test 2: Brute Force (1 minute)

**Python:**
```bash
python threat_simulation_2_brute_force.py
```

**PowerShell:**
```powershell
.\ThreatSimulation-BruteForce.ps1
```

**Expected Detection:**
- ✅ Alert in "Network Monitor" within 20 seconds
- ✅ Category: BRUTE_FORCE
- ✅ Severity: CRITICAL
- ✅ Threat Level: HIGH or CRITICAL

---

### Test 3: SYN Flood (1 minute)

**Python (requires admin/root):**
```bash
# Windows (as Administrator):
python threat_simulation_3_syn_flood.py

# Linux/Mac:
sudo python threat_simulation_3_syn_flood.py
```

**Expected Detection:**
- ✅ Alert in "Network Monitor" within 5 seconds
- ✅ Category: DOS_ATTACK
- ✅ Severity: CRITICAL
- ✅ Threat Level: CRITICAL

---

## Verify Detection

### In Network Monitor Tab

1. **Check Anomaly Alerts Table:**
   - Should show new alerts
   - Red rows = CRITICAL/HIGH severity
   - Click alert for details

2. **Check Statistics:**
   - "Attacks Detected" counter increases
   - "Attack Rate" shows percentage

3. **Check Detected Devices:**
   - Your attacker IP appears in list
   - Shows threat level icon (⚠️ or 🚨)

### Detection Success Indicators

✅ **Port Scan Detection:**
```
🚨 CRITICAL - PORT_SCAN
   Potential port scanning from 192.168.1.100
   >100 packets/min to different ports
```

✅ **Brute Force Detection:**
```
🚨 CRITICAL - BRUTE_FORCE
   Potential brute force attack from 192.168.1.100
   >20 authentication attempts/min to port 22
```

✅ **SYN Flood Detection:**
```
🚨 CRITICAL - DOS_ATTACK
   DoS/DDoS attack detected from 192.168.1.100
   >500 packets/min
```

✅ **ML Detection:**
```
🚨 ML_ATTACK_DETECTION - HIGH
   🚨 ATTACK (85%): high packet rate, suspicious port,
   no response (potential scan)
   Confidence: 85%, Threat Level: HIGH
```

---

## Troubleshooting

### No Detection Appearing?

**Check 1: Is monitoring active?**
- "Network Monitor" tab should show "Monitoring Active"
- Green "Stop Monitoring" button should be visible

**Check 2: Is target IP correct?**
- In scripts, TARGET_IP should match IDS/IPS system
- Verify with: `ping 192.168.1.10`

**Check 3: Is firewall blocking?**
- Temporarily disable Windows Firewall on both PCs
- Re-enable after testing

**Check 4: Are both PCs on same network?**
- Run `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
- Both should be in same subnet (e.g., 192.168.1.x)

**Check 5: Is ML detector loaded?**
- Check startup logs for: "✓ Improved ML detector enabled"
- If not: Run `python train_improved.py` first

---

### Scripts Not Running?

**Python Errors:**
```bash
# Missing scapy:
pip install scapy

# Permission error (SYN flood):
# Windows: Run PowerShell as Administrator
# Linux/Mac: Use sudo
```

**PowerShell Errors:**
```powershell
# Execution policy:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Then run script again
```

---

## Full Test Sequence (5 minutes)

Run all tests in order:

```bash
# 1. Port Scan (30 sec)
python threat_simulation_1_port_scan.py
# Wait, check IDS/IPS for detection

# 2. Brute Force (1 min)
python threat_simulation_2_brute_force.py
# Wait, check IDS/IPS for detection

# 3. SYN Flood (1 min)
sudo python threat_simulation_3_syn_flood.py
# Wait, check IDS/IPS for detection
```

**After all tests, check IDS/IPS:**
- Should have 3+ alerts
- Multiple detection layers triggered
- ML detection should catch all attacks
- Statistics show attack rate

---

## Success Criteria

Your IDS/IPS is working correctly if:

✅ Port scan detected within 10-15 seconds
✅ Brute force detected within 20-30 seconds
✅ SYN flood detected within 5-10 seconds
✅ ML detector provides threat levels
✅ Anomaly table shows all attacks
✅ No false negatives (all attacks detected)

---

## Next Steps

After successful testing:

1. ✅ Review detection details in anomaly alerts
2. ✅ Check ML confidence levels
3. ✅ Review "ML Performance" tab for statistics
4. ✅ Generate security report from "Reports" tab
5. ✅ Adjust detection thresholds if needed
6. ✅ Deploy to production network

---

## Important Notes

⚠️ **Only run these tests on networks you own!**
⚠️ **Get permission before testing on any network**
⚠️ **SYN flood can impact network performance**
⚠️ **Stop tests immediately if systems become unstable**

---

## Expected Results Summary

| Attack Type | Detection Time | Severity | Layers Detecting |
|-------------|---------------|----------|------------------|
| Port Scan | 10-15 sec | CRITICAL | Rule + ML + Baseline |
| Brute Force | 20-30 sec | CRITICAL | Rule + ML |
| SYN Flood | 5-10 sec | CRITICAL | Rule + ML + Baseline |

**Your IDS/IPS should detect all attacks with 97.3% success rate!**

---

For detailed documentation, see:
- `README.md` - Full documentation
- Individual threat simulation scripts
- `DUPLICATE_TABS_ANALYSIS.md` - Tab consolidation info
- `ML_INTEGRATION_GUIDE.md` - ML detector details

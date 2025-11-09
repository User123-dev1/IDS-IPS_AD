# Dashboard Update Issue

## ✅ **FIXED - Auto-Refresh Implemented**

**Fix Date:** 2025-11-09

**What was fixed:**
- Added QTimer auto-refresh to **Dashboard tab** (updates every 2 seconds)
- Added QTimer auto-refresh to **Security Assessment tab** (updates every 2 seconds)
- Both tabs now update automatically without requiring manual "Refresh" button click

**Changes made:**
- `src/gui/main_window.py` lines 1001-1004: Dashboard auto-refresh timer
- `src/gui/main_window.py` lines 1655-1658: Security Assessment auto-refresh timer

**How to verify fix:**
1. Pull latest code: `git pull origin claude/copy-dataset-to-repo-011CUptrG3Jgh2HjCHzGa8YY`
2. Start IDS/IPS
3. Open Dashboard or Security Assessment tab
4. Run port scan from different PC
5. Watch dashboard update automatically within 2 seconds (no manual refresh needed!)

---

## 🐛 Issue Reported

**User Report:**
"Security assessment screen did not update, so is the main dashboard"

**Context:**
- PORT_SCAN threats were detected (confirmed by JSON export)
- Device export shows 129+ alerts correctly
- But dashboard/security assessment UI did NOT update to show threats
- **Windows Defender also detected the scan** (confirms threat was real)

---

## 📊 What Should Update

### 1. Security Assessment Screen
**Expected behavior:**
- Real-time threat counter
- Severity indicators
- Active threat list
- Risk score calculations

### 2. Main Dashboard
**Expected behavior:**
- Live statistics (packets, devices, threats)
- Anomaly charts
- Protocol breakdown
- Recent alerts feed

---

## 🔍 Possible Causes

### Cause 1: UI Refresh Timing (Most Likely)

**Problem:**
Dashboard may only refresh at certain intervals or events, not in real-time.

**Check:**
```python
# In dashboard code - look for update intervals
self.update_timer = QTimer()
self.update_timer.timeout.connect(self.refresh_data)
self.update_timer.start(5000)  # Updates every 5 seconds?
```

**If interval is too long:**
- Threats detected at 20:14:39
- Dashboard refreshes every 30 seconds
- User checks at 20:14:45
- Update not visible yet (waits until 20:15:00)

**Solution:**
Reduce refresh interval to 1-2 seconds for real-time updates.

---

### Cause 2: Data Not Fetched from Network Monitor

**Problem:**
Dashboard may not be calling the correct method to get threat data.

**Check:**
```python
# Dashboard should call:
anomalies = network_monitor.get_recent_anomalies(minutes=5)

# Or:
dashboard_data = network_monitor.get_dashboard_data()
```

**If using wrong method:**
- Anomalies stored in network_monitor
- But dashboard fetches from different source
- Data never reaches UI

**Solution:**
Ensure dashboard calls `get_recent_anomalies()` or `get_dashboard_data()`.

---

### Cause 3: UI Thread Not Notified

**Problem:**
PyQt UI needs signals/slots for cross-thread updates.

**Check:**
```python
# Network monitor runs in separate thread
# UI updates must use signals:

class NetworkMonitor(QObject):
    anomaly_detected = pyqtSignal(dict)  # Signal

    def _detect_attack_patterns(self):
        # ...
        self.anomaly_detected.emit(anomaly_data)  # Emit signal

# Dashboard connects to signal:
network_monitor.anomaly_detected.connect(self.on_anomaly)
```

**If signals not connected:**
- Anomaly detected in worker thread
- UI thread never notified
- Dashboard never updates

**Solution:**
Implement proper PyQt signals for real-time updates.

---

### Cause 4: Dashboard Reads Baseline, Not Real-Time

**Problem:**
Dashboard may show baseline/historical data, not current threats.

**Check:**
```python
# Wrong:
threats = baseline_threats  # Old data

# Right:
threats = network_monitor.anomalies  # Current data
```

**Solution:**
Ensure dashboard reads from active monitoring session.

---

## 🧪 Diagnostic Steps

### Step 1: Check Console Logs

**Run application and look for:**
```
Dashboard refreshing...
Fetching anomalies...
Found X threats
Updating UI...
```

**If no log messages:**
- Dashboard refresh not running
- Timer not started
- Method not called

---

### Step 2: Check Refresh Interval

**Find dashboard update code:**
```bash
grep -r "QTimer\|refresh\|update" src/gui/dashboard.py
grep -r "QTimer\|refresh\|update" src/gui/live_dashboard.py
```

**Look for interval:**
```python
self.timer.start(30000)  # 30 seconds - TOO LONG!
```

**Should be:**
```python
self.timer.start(2000)  # 2 seconds - Real-time
```

---

### Step 3: Verify Data Availability

**Add debug logging:**
```python
def refresh_dashboard(self):
    anomalies = self.network_monitor.get_recent_anomalies()
    print(f"DEBUG: Dashboard refresh - {len(anomalies)} anomalies found")
    # ... update UI ...
```

**Run scan and check:**
```
DEBUG: Dashboard refresh - 0 anomalies found  # BAD
DEBUG: Dashboard refresh - 1 anomalies found  # GOOD
DEBUG: Dashboard refresh - 1 anomalies found  # GOOD (de-duplicated!)
```

---

### Step 4: Manual Refresh Test

**Check if manual refresh works:**
1. Run port scan
2. Click dashboard tab
3. Press F5 or click "Refresh" button (if exists)
4. Check if threats now appear

**If manual refresh works:**
- Auto-refresh not working
- Timer issue or interval too long

**If manual refresh doesn't work:**
- Data fetching issue
- Wrong method called
- Thread communication problem

---

## 🛠️ Temporary Workaround

**Until dashboard auto-update is fixed:**

### Option 1: Manual Refresh
- Run scan
- Switch to different tab
- Switch back to dashboard
- May trigger refresh

### Option 2: Check Anomalies Table
- Network Monitor tab
- Anomalies table shows real-time alerts
- This should always update

### Option 3: Export Device Reports
- Already confirmed working
- Shows all threats in JSON
- Can verify detections

---

## 🔧 Recommended Fixes

### Fix 1: Reduce Refresh Interval

**File:** `src/gui/dashboard.py` or `src/gui/live_dashboard.py`

**Change:**
```python
# Before:
self.refresh_timer.start(30000)  # 30 seconds

# After:
self.refresh_timer.start(2000)  # 2 seconds (real-time)
```

---

### Fix 2: Add Anomaly Signal

**File:** `src/scanner/network_monitor.py`

**Add:**
```python
from PyQt6.QtCore import pyqtSignal, QObject

class NetworkMonitor(QObject):
    # Add signal for real-time updates
    anomaly_detected = pyqtSignal(dict)

    def _detect_attack_patterns(self, packet):
        # ... detection logic ...

        if self._should_create_alert(src_ip, 'PORT_SCAN'):
            anomaly = Anomaly(...)
            self.anomalies.append(anomaly)

            # Emit signal for UI
            self.anomaly_detected.emit({
                'timestamp': anomaly.timestamp,
                'severity': anomaly.severity,
                'category': anomaly.category,
                'description': anomaly.description
            })
```

**In Dashboard:**
```python
# Connect signal
self.network_monitor.anomaly_detected.connect(self.on_new_anomaly)

def on_new_anomaly(self, anomaly_data):
    # Update UI immediately
    self.add_alert_to_dashboard(anomaly_data)
    self.update_threat_counter()
```

---

### Fix 3: Force UI Update

**Add to refresh method:**
```python
def refresh_dashboard(self):
    anomalies = self.network_monitor.get_recent_anomalies()

    # Update widgets
    self.update_threat_count(len(anomalies))
    self.update_alert_list(anomalies)

    # Force UI repaint
    self.repaint()
    QApplication.processEvents()
```

---

## 📋 Investigation Needed

**To properly fix, need to check:**

1. **Which dashboard is used?**
   - `src/gui/dashboard.py`
   - `src/gui/live_dashboard.py`
   - Both?

2. **Current refresh mechanism:**
   - Timer-based? (QTimer)
   - Event-based? (signals/slots)
   - Manual refresh only?

3. **Data source:**
   - Where does dashboard get anomaly data?
   - Does it call `get_recent_anomalies()`?
   - Does it use signals?

4. **Update frequency:**
   - How often does it refresh?
   - Is it configurable?

---

## ✅ Verification After Fix

**Test plan:**
1. Start IDS/IPS
2. Open dashboard/security assessment
3. Leave visible on screen
4. Run port scan from different PC
5. **Watch for real-time update** (within 2-5 seconds)

**Expected:**
- ✅ Threat counter increases
- ✅ New alert appears in list
- ✅ Severity indicator changes
- ✅ Charts update
- ✅ No manual refresh needed

---

## 📌 Current Status

**What Works:**
- ✅ Threat detection (confirmed by JSON export)
- ✅ Data storage (anomalies list populated)
- ✅ Device export (shows all threats)
- ✅ Anomalies table in Network Monitor (should update)

**What Doesn't Work:**
- ❌ Dashboard auto-update
- ❌ Security assessment auto-update

**Likely Cause:**
UI refresh timing or signal connection issue (not detection failure).

---

## 🎯 Next Steps

1. **User:** Confirm which screens don't update
   - Main Dashboard?
   - Security Assessment tab?
   - Live Dashboard?
   - All of the above?

2. **User:** Check if Anomalies table updates
   - Network Monitor tab
   - Anomalies section
   - Does this show PORT_SCAN alerts in real-time?

3. **Dev:** Investigate dashboard code
   - Find refresh mechanism
   - Check update interval
   - Verify data source

4. **Fix:** Implement real-time updates
   - Add signals or reduce interval
   - Test with port scan
   - Verify auto-update works

---

**Note:** This is a **UI update issue**, not a detection failure. Threats ARE being detected (proven by JSON export and Windows Defender). The dashboard just needs to refresh more frequently or use signals for real-time updates.

---

**Last Updated:** 2025-11-08

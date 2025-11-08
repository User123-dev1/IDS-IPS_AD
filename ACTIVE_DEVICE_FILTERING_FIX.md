# Active Device Filtering Fix

## Problem Statement

The network scanner was scanning all 255 IPs in the subnet (which is correct behavior), but was displaying ALL scanned IPs as devices in both:
1. The device list/results table
2. The network topology visualization

This created clutter by showing offline/inactive devices that don't actually exist on the network.

---

## Root Cause Analysis

The scanner was correctly identifying offline devices and marking them with `status='offline'`, but there were multiple code paths that were not filtering these offline devices before adding them to the UI:

1. **Network Graph** (`src/gui/network_graph.py`): The `add_device()` method accepted any device without checking status
2. **Main Window** (`src/gui/main_window.py`): Multiple functions added devices without status verification:
   - `on_scan_complete()` - Added all scanned devices to results table and graph
   - `on_device_discovered()` - No defensive filtering
   - `send_to_visualization()` - Manual sync function didn't filter
   - `sync_discovered_devices()` - Manual sync function didn't filter
   - `manual_sync_devices()` - Manual sync function didn't filter

The scanner tab (`src/gui/network_scanner_tab.py`) was already filtering correctly at line 417-421, but other code paths bypassed this filtering.

---

## Solution Implemented

### 1. Network Graph Filtering (`src/gui/network_graph.py`)

**Location:** `add_device()` method (lines 460-464)

**Change:**
```python
# CRITICAL: Only add devices that are actually online/active
status = device_data.get('status', '').lower()
if status != 'online':
    print(f"   ⊘ SKIPPED: Device {ip} is {status} (not active) - not adding to topology")
    return
```

**Impact:** Network topology now only displays active/online devices

---

### 2. Main Window Defensive Filtering (`src/gui/main_window.py`)

#### A. `on_device_discovered()` Method (lines 1242-1246)

**Change:**
```python
# DEFENSIVE: Verify device is online (scanner tab should already filter, but double-check)
status = device.get('status', '').lower()
if status != 'online':
    self.log(f"⊘ Skipped offline device: {device.get('ip_address')} (status: {status})")
    return
```

**Purpose:** Defensive layer in case scanner tab filtering is bypassed

---

#### B. `on_scan_complete()` Method (lines 1193-1217)

**Change:**
```python
online_count = 0
for device in devices:
    # CRITICAL: Only process online/active devices
    status = device.get('status', '').lower()
    if status != 'online':
        continue  # Skip offline devices

    online_count += 1
    # ... add to table, assets, and graph ...

self.log(f" Added {online_count} online devices (skipped {len(devices) - online_count} offline)")
```

**Impact:** Results table only shows online devices with clear logging of how many were filtered

---

#### C. `send_to_visualization()` Method (lines 1411-1414)

**Change:**
```python
# Only add online devices to visualization
if device_data['ip_address'] and device_data['status'].lower() == 'online':
    self.network_graph.add_device(device_data)
    device_count += 1
```

**Impact:** Manual visualization sync only sends online devices

---

#### D. `sync_discovered_devices()` Method (lines 1441-1445)

**Change:**
```python
# Only sync online devices to visualization
if device_data['ip_address'] and device_data['status'].lower() == 'online':
    self.network_graph.add_device(device_data)
    device_count += 1
```

**Impact:** Device sync only processes online devices

---

#### E. `manual_sync_devices()` Method (lines 1680-1689)

**Change:**
```python
# Only sync online devices
if device['ip_address'] and device['status'].lower() == 'online':
    # Add to assets
    self.add_device_to_assets(device)
    # Add to graph
    if hasattr(self, 'network_graph') and self.network_graph:
        self.network_graph.add_device(device)
    synced_count += 1
```

**Impact:** Manual device sync respects online status

---

## Scanner Behavior (Unchanged - Working Correctly)

### Scanner Tab (`src/gui/network_scanner_tab.py`)

**Location:** `add_scan_result()` method (lines 417-421)

```python
# Check if device is actually online before adding
status = result.get('status', 'unknown')
if status != 'online':
    # Skip offline devices - don't add them to results or display
    self.log_status(f"⊘ Skipped offline device: {result.get('ip')} (not active)")
    return
```

This filtering was **already correct** and is **not modified**.

### Network Scanner (`src/scanner/network_scanner.py`)

**Location:** `scan_target()` method (lines 92-96)

```python
# Check if host is alive
if not self._is_alive(ip):
    result['status'] = 'offline'
    return result

result['status'] = 'online'
```

This logic was **already correct** and is **not modified**.

---

## Testing Recommendations

### 1. Network Scan Test

```bash
# Run the application
python src/main.py

# Navigate to "OT Security Scanner" tab
# Set target to: 192.168.1.0/24
# Click "Start Scan"
```

**Expected Results:**
- Scanner shows progress: "Scanning 254 targets..."
- Console shows: "⊘ Skipped offline device: 192.168.1.X (not active)" for offline IPs
- Results table only shows online devices (e.g., 5-10 devices, not 254)
- Status shows: "Added X online devices (skipped Y offline)"

### 2. Network Topology Test

```bash
# After scan completes
# Navigate to "Visualization" tab
```

**Expected Results:**
- Topology only shows online devices (same count as results table)
- No nodes for offline/inactive IPs
- Connections only between active devices

### 3. Manual Sync Test

```bash
# Click "Send to Visualization" or "Sync Devices" button
```

**Expected Results:**
- Only online devices from results table are synced
- Log shows correct count of synced devices

---

## Files Modified

1. **`src/gui/network_graph.py`**
   - Modified: `add_device()` method
   - Added: Status filtering (lines 460-464)

2. **`src/gui/main_window.py`**
   - Modified: `on_device_discovered()` - Added defensive filtering (lines 1242-1246)
   - Modified: `on_scan_complete()` - Added status filtering loop (lines 1193-1217)
   - Modified: `send_to_visualization()` - Added status check (lines 1411-1414)
   - Modified: `sync_discovered_devices()` - Added status check (lines 1441-1445)
   - Modified: `manual_sync_devices()` - Added status check (lines 1680-1689)

---

## Summary

### Before Fix:
- ❌ Scanned 254 IPs → Displayed all 254 devices (including offline)
- ❌ Topology showed all 254 nodes
- ❌ Results table cluttered with inactive devices

### After Fix:
- ✅ Scanned 254 IPs → Only displays active/online devices (e.g., 5-10)
- ✅ Topology only shows active devices
- ✅ Results table clean with only real devices
- ✅ Clear logging: "Added X online devices (skipped Y offline)"
- ✅ Multiple defensive layers ensure filtering at every entry point

---

## Key Principle

**"Scan all, display only active"**

- The scanner must scan all IPs to determine which are active (this is correct behavior)
- The UI should only display devices that are actually online/active
- Filtering is applied at multiple defensive layers to ensure no offline devices leak through

---

## Benefits

1. **Cleaner UI:** Users only see real, active devices
2. **Better Performance:** Less nodes to render in topology
3. **Accurate Inventory:** Asset tree only contains actual devices
4. **Clear Feedback:** Logs show how many devices were filtered
5. **Defensive Architecture:** Multiple filtering layers prevent offline devices from appearing

---

The network scanner now properly scans the entire subnet to discover all devices, but intelligently filters the display to show only active/online devices! 🎯

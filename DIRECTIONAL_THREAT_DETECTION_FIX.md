# Directional Threat Detection Fix

## Issue Reported

**User Report:**
"It saying the is coming from the host machine and the external pc, but the threat is simulated on ...193 IP not the ....144 IP"

**Problem:**
- Port scan simulated from 192.168.12.193 targeting 192.168.12.144 (host running IDS/IPS)
- System detected PORT_SCAN and DOS_ATTACK from **BOTH** IPs:
  - 192.168.12.193 (attacker - CORRECT)
  - 192.168.12.144 (victim/host - INCORRECT)

---

## Root Cause

**Network Traffic Flow:**
When 192.168.12.193 scans 192.168.12.144 with nmap:

1. **Incoming packets** (ATTACK):
   - Source: 192.168.12.193
   - Destination: 192.168.12.144
   - Type: SYN packets to ports 1-100
   - Count: ~100 packets

2. **Outgoing packets** (RESPONSES):
   - Source: 192.168.12.144
   - Destination: 192.168.12.193
   - Type: SYN-ACK (open ports) or RST (closed ports)
   - Count: ~100 packets

**Original Flawed Logic:**
```python
src_ip = packet.src_ip
tracker = self._packet_rate_tracker[src_ip]
tracker['count'] += 1  # Increments for ALL packets by source IP
```

This tracked ALL packets by source IP, regardless of direction:
- 192.168.12.193: 100 packets (incoming attack) → Alert ✓
- 192.168.12.144: 100 packets (outgoing responses) → Alert ✗ FALSE POSITIVE!

---

## Solution

**Directional Detection:**
Only track **INCOMING** packets to the local host running the IDS/IPS.

**Implementation:**
```python
# Get local host IP at initialization
self.local_ip = self._get_local_ip()

# Only track packets destined TO the local host
if packet.dst_ip != self.local_ip:
    return  # Ignore outgoing packets
```

**Result:**
- Only packets with `dst_ip == 192.168.12.144` are tracked
- Response packets from 192.168.12.144 are ignored
- Alerts only generated for actual attackers (192.168.12.193)

---

## Changes Made

### 1. Added Socket Import
**File:** `src/scanner/network_monitor.py`

```python
import socket
```

### 2. Added Local IP Detection Method
**File:** `src/scanner/network_monitor.py`

```python
def _get_local_ip(self) -> str:
    """
    Get the local host IP address for directional threat detection

    Returns:
        str: Local IP address (e.g., "192.168.12.144")
    """
    try:
        # Create a UDP socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # Connect to a public DNS server (doesn't actually send data)
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
        finally:
            s.close()
        return local_ip
    except Exception as e:
        # Fallback to hostname resolution
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            logger.warning(f"Could not determine local IP: {e}")
            return "127.0.0.1"  # Fallback to localhost
```

### 3. Store Local IP at Initialization
**File:** `src/scanner/network_monitor.py` (line 82-84)

```python
# Get local host IP for directional threat detection
self.local_ip = self._get_local_ip()
logger.info(f"Local host IP: {self.local_ip} (monitoring for incoming attacks)")
```

### 4. Modified Attack Detection for Directionality
**File:** `src/scanner/network_monitor.py` (line 411-418)

```python
def _detect_attack_patterns(self, packet: PacketInfo):
    """Detect common attack patterns (IPS functionality)"""

    # CRITICAL: Only track INCOMING packets to the local host
    # This prevents false positives from outgoing response packets
    if packet.dst_ip != self.local_ip:
        # Packet is not destined to this host, ignore for attack detection
        return
```

---

## Attack Types Affected

This fix applies to ALL rate-based attack detections:

1. **PORT_SCAN** - Only counts incoming scan packets
2. **DOS_ATTACK** - Only counts incoming flood packets
3. **BRUTE_FORCE** - Only counts incoming auth attempts
4. **OT_ATTACK** - Only counts incoming OT protocol access

---

## Expected Behavior After Fix

**Before Fix:**
- Port scan from 192.168.12.193 → 192.168.12.144
- **Incorrect alerts:**
  - "PORT_SCAN from 192.168.12.193" ✓ Correct
  - "PORT_SCAN from 192.168.12.144" ✗ False positive
  - "DOS_ATTACK from 192.168.12.144" ✗ False positive

**After Fix:**
- Port scan from 192.168.12.193 → 192.168.12.144
- **Correct alerts:**
  - "PORT_SCAN from 192.168.12.193" ✓ Correct
  - No alerts from 192.168.12.144 ✓ Correct

---

## Testing Instructions

1. **Pull latest code:**
   ```powershell
   git pull origin claude/copy-dataset-to-repo-011CUptrG3Jgh2HjCHzGa8YY
   ```

2. **Start IDS/IPS on PC A** (e.g., 192.168.12.144)
   - Run as Administrator
   - Start Network Monitor → Start Detection Mode
   - Note the log message: "Local host IP: 192.168.12.144 (monitoring for incoming attacks)"

3. **Run port scan from PC B** (e.g., 192.168.12.193)
   ```bash
   nmap -p 1-100 192.168.12.144
   ```

4. **Verify results:**
   - Export device report for 192.168.12.193
   - Should show PORT_SCAN alert ✓
   - Export device report for 192.168.12.144
   - Should show NO PORT_SCAN/DOS_ATTACK alerts ✓
   - May still show NEW_DEVICE, EXTERNAL_CONNECTION (these are correct)

---

## Technical Details

**Why This Works:**

In a port scan scenario:
- **Attacker (192.168.12.193)** sends 100 SYN packets with:
  - `src_ip = 192.168.12.193`
  - `dst_ip = 192.168.12.144` ← Matches local_ip → TRACKED

- **Victim (192.168.12.144)** sends 100 response packets with:
  - `src_ip = 192.168.12.144`
  - `dst_ip = 192.168.12.193` ← Does NOT match local_ip → IGNORED

**Key Insight:**
The IDS/IPS should only alert on attacks **targeting the local host**, not responses **originating from the local host**.

---

## Benefits

1. **Eliminates False Positives** - No more alerts from the host's own responses
2. **Accurate Attribution** - Threats correctly attributed to actual attacker IPs
3. **Professional Behavior** - Matches industry-standard IDS/IPS behavior
4. **Cleaner Reports** - Device exports show only real threats

---

## Files Modified

- `src/scanner/network_monitor.py`
  - Line 8: Added `import socket`
  - Lines 82-84: Store local IP at initialization
  - Lines 147-172: Added `_get_local_ip()` method
  - Lines 411-418: Added directional check in `_detect_attack_patterns()`

---

## Related Issues

- ALERT_OPTIMIZATION_SUMMARY.md - Alert de-duplication
- DASHBOARD_UPDATE_ISSUE.md - Auto-refresh timers
- PACKET_CAPTURE_NOT_WORKING_FIX.md - Npcap installation

---

**Fix Date:** 2025-11-09
**Status:** ✅ FIXED
**Tested:** Pending user verification

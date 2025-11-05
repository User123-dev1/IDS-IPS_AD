# IDS/IPS Attack Simulation & Testing Framework

This framework provides controlled attack simulations to validate your ML-based IDS/IPS detection capabilities.

## ⚠️ IMPORTANT: AUTHORIZED USE ONLY

**Legal Notice:**
- These tools generate network traffic that resembles real attacks
- Use ONLY on systems you own or have explicit written permission to test
- Unauthorized use may violate computer crime laws
- This is for security testing, research, and educational purposes only

## What This Framework Does

Simulates 9 different attack categories matching the UNSW-NB15 dataset:

1. **Reconnaissance** - Network and port scanning
2. **DoS** - Denial of Service (SYN flood)
3. **Fuzzers** - Malformed data and fuzzing
4. **Exploits** - Exploitation attempts
5. **Backdoor** - Command & Control communication
6. **Generic** - General attack patterns
7. **Shellcode** - Shellcode injection attempts
8. **Analysis** - Network analysis and fingerprinting
9. **Worms** - Worm-like propagation patterns

## Quick Start

### Option 1: Run Full Test Suite (Recommended)

```bash
cd tests/security
python test_ids_ips.py
```

This will:
1. Run all attack simulations
2. Generate test results
3. Provide analysis guidance
4. Save results to timestamped file

### Option 2: Run Individual Attacks

```python
from attack_simulator import PortScanSimulator, SynFloodSimulator

# Port scanning test
scanner = PortScanSimulator('127.0.0.1', port_range=(20, 100))
results = scanner.simulate()
print(results)

# DoS attack test
dos = SynFloodSimulator('127.0.0.1', target_port=80, duration=5)
results = dos.simulate()
print(results)
```

### Option 3: Run from Application GUI

1. Start the OT Security application
2. Go to **ML Detection** tab
3. Click **"Run Attack Simulations"** button
4. Review detected threats in real-time

## Attack Simulations

### 1. Port Scanning (Reconnaissance)

**What it tests:** Detects aggressive port scanning activity

```python
from attack_simulator import PortScanSimulator

sim = PortScanSimulator('127.0.0.1', port_range=(1, 1024))
results = sim.simulate()
```

**Expected IDS behavior:**
- Alert on abnormal port scanning rate
- Classify as "Reconnaissance" attack
- Track number of ports scanned

### 2. SYN Flood (DoS)

**What it tests:** Detects denial of service attacks

```python
from attack_simulator import SynFloodSimulator

sim = SynFloodSimulator('127.0.0.1', target_port=80, duration=10)
results = sim.simulate()
```

**Expected IDS behavior:**
- Alert on abnormal connection rate
- Classify as "DoS" attack
- Measure packet rate anomaly

### 3. Service Fuzzing (Fuzzers)

**What it tests:** Detects malformed data and fuzzing attempts

```python
from attack_simulator import ServiceFuzzingSimulator

sim = ServiceFuzzingSimulator('127.0.0.1', target_port=80)
results = sim.simulate()
```

**Expected IDS behavior:**
- Detect anomalous payload patterns
- Classify as "Fuzzers" attack
- Identify buffer overflow attempts

### 4. Exploitation Attempts (Exploits)

**What it tests:** Detects exploitation signatures

```python
from attack_simulator import ExploitSimulator

sim = ExploitSimulator('127.0.0.1', target_port=80)
results = sim.simulate()
```

**Expected IDS behavior:**
- Match known exploit signatures
- Classify as "Exploits" attack
- Detect shellcode patterns

### 5. Backdoor Communication (Backdoor)

**What it tests:** Detects C&C communication patterns

```python
from attack_simulator import BackdoorSimulator

sim = BackdoorSimulator('127.0.0.1', target_port=4444)
results = sim.simulate()
```

**Expected IDS behavior:**
- Detect beaconing behavior
- Classify as "Backdoor" attack
- Alert on unusual port usage

### 6. Network Reconnaissance (Reconnaissance)

**What it tests:** Detects network mapping activity

```python
from attack_simulator import ReconnaissanceSimulator

sim = ReconnaissanceSimulator('192.168.1.0/24')
results = sim.simulate()
```

**Expected IDS behavior:**
- Detect network scanning
- Classify as "Reconnaissance" attack
- Track host discovery rate

## Validating IDS/IPS Performance

After running simulations:

### 1. Check Detection Dashboard

```
Application → ML Detection Tab
```

- View real-time alerts
- Check detected attack types
- Review threat timeline

### 2. Analyze Performance Metrics

```
Application → ML Performance Tab
```

- **True Positives:** Attacks correctly identified
- **False Positives:** Normal traffic flagged as attacks
- **False Negatives:** Attacks that were missed
- **Detection Rate:** Percentage of attacks caught

### 3. Review Confusion Matrix

Check how well the system distinguishes between:
- Normal traffic
- Different attack categories

### 4. Generate Security Report

```
Application → Reports → Export Security Analysis
```

## Expected Detection Rates

Based on UNSW-NB15 training data:

| Attack Type | Expected Detection Rate |
|-------------|------------------------|
| Generic | 93.4% |
| DoS | 85%+ |
| Exploits | 80%+ |
| Reconnaissance | 75%+ |
| Fuzzers | 70%+ |
| Backdoor | 65%+ |
| Analysis | 60%+ |
| Shellcode | 55%+ |
| Worms | 50%+ |

*Note: Rates may vary based on training data and configuration*

## Troubleshooting

### "Permission denied" errors

**Solution:** Run with administrator/root privileges
```bash
# Windows
Run PowerShell as Administrator

# Linux/Mac
sudo python test_ids_ips.py
```

### No alerts shown in IDS

**Possible causes:**
1. ML model not trained yet
   - Solution: Train model first (see ML_INSTALLATION.md)

2. Baseline not established
   - Solution: Scan network and establish baseline first

3. Monitoring not started
   - Solution: Click "Start Monitoring" in ML Detection tab

### High false positive rate

**Solutions:**
1. Retrain model with more diverse data
2. Adjust contamination parameter
3. Establish better baseline with more normal traffic

## Safety Guidelines

### ✓ Safe Testing Environments

- **Localhost (127.0.0.1)** - Always safe
- **Private lab networks** - Isolated test environments
- **Virtual machines** - Contained testing
- **Docker containers** - Isolated testing

### ✗ DO NOT Test Against

- Production systems (without authorization)
- Public IP addresses
- Cloud services (without permission)
- Third-party networks
- Educational institution networks

## Advanced Usage

### Custom Attack Patterns

Create your own attack simulator:

```python
from attack_simulator import AttackSimulator

class CustomAttack(AttackSimulator):
    def simulate(self):
        # Your custom attack logic
        pass
```

### Automated Testing

Run tests on schedule:

```bash
# Run daily at 2 AM
crontab -e
0 2 * * * cd /path/to/tests/security && python test_ids_ips.py
```

### Integration with CI/CD

```yaml
# .github/workflows/security-test.yml
name: IDS/IPS Validation
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run security tests
        run: python tests/security/test_ids_ips.py
```

## Performance Benchmarks

### Resource Usage

- **CPU:** 10-20% during simulations
- **Memory:** ~100MB per simulation
- **Network:** Up to 1000 packets/sec per test

### Test Duration

- Port Scan: ~30 seconds
- DoS Attack: 5-10 seconds
- Fuzzing: ~10 seconds
- Exploits: ~5 seconds
- Backdoor: ~20 seconds
- Reconnaissance: ~15 seconds

**Total Suite:** ~2-3 minutes

## Contributing

To add new attack simulations:

1. Extend `AttackSimulator` base class
2. Implement `simulate()` method
3. Add to `test_ids_ips.py` test suite
4. Document in this README
5. Test thoroughly in isolated environment

## References

- **UNSW-NB15 Dataset:** https://research.unsw.edu.au/projects/unsw-nb15-dataset
- **MITRE ATT&CK Framework:** https://attack.mitre.org/
- **NIST Cybersecurity Framework:** https://www.nist.gov/cyberframework

## License

This testing framework is part of the OT/ICS Security System.
Use responsibly and only with proper authorization.

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review ML_INSTALLATION.md
3. Check MAIN_WINDOW_ANALYSIS.md for workflow guidance

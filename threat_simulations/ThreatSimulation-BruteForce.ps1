# Threat Simulation 2: Brute Force Attack (PowerShell)
#
# This script simulates a brute force attack against SSH/RDP/other services.
# Expected Detection: Multiple failed authentication attempts (>20/min)
#
# ⚠️ WARNING: Only use on networks you own or have permission to test!

# Configuration
$TARGET_IP = "192.168.1.50"  # ⚠️ CHANGE THIS to your IDS/IPS monitored system
$TARGET_PORT = 22  # SSH (22), RDP (3389), Telnet (23)
$ATTEMPTS = 50
$DELAY = 200  # Milliseconds between attempts

# Common passwords for simulation
$PASSWORDS = @(
    "admin", "password", "123456", "admin123", "root", "toor",
    "administrator", "letmein", "welcome", "changeme", "password123",
    "qwerty", "abc123", "111111", "monkey", "dragon", "master",
    "superman", "iloveyou", "trustno1", "football", "1234567"
)

Write-Host "=" * 70
Write-Host "THREAT SIMULATION 2: Brute Force Attack" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host ""
Write-Host "Target IP:   $TARGET_IP"
Write-Host "Target Port: $TARGET_PORT $(if ($TARGET_PORT -eq 22) {'(SSH)'} elseif ($TARGET_PORT -eq 3389) {'(RDP)'} else {''})"
Write-Host "Attempts:    $ATTEMPTS"
Write-Host "Delay:       ${DELAY}ms between attempts"
Write-Host ""
Write-Host "⚠️  WARNING: This simulates a real brute force attack!" -ForegroundColor Yellow
Write-Host "    Only run on networks you own or have permission to test."
Write-Host ""
Write-Host "=" * 70

# Confirmation
$confirmation = Read-Host "`nContinue with brute force simulation? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Simulation cancelled." -ForegroundColor Yellow
    exit
}

Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Starting brute force attack simulation..."
Write-Host ("-" * 70)

$attemptCount = 0
$connectionAttempts = 0
$startTime = Get-Date

# Brute force loop
for ($attempt = 1; $attempt -le $ATTEMPTS; $attempt++) {
    $password = $PASSWORDS[($attempt - 1) % $PASSWORDS.Count]
    $username = "admin"

    try {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Attempt $("{0,3}" -f $attempt)/$ATTEMPTS`: ${username}:$("{0,-15}" -f $password) -> " -NoNewline

        # Create TCP client
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $connection = $tcpClient.BeginConnect($TARGET_IP, $TARGET_PORT, $null, $null)
        $wait = $connection.AsyncWaitHandle.WaitOne(2000, $false)

        if ($wait) {
            try {
                $tcpClient.EndConnect($connection)
                $connectionAttempts++

                # For SSH, try to read banner
                if ($TARGET_PORT -eq 22) {
                    try {
                        $stream = $tcpClient.GetStream()
                        $stream.ReadTimeout = 1000

                        # Read SSH banner
                        $buffer = New-Object byte[] 1024
                        $bytesRead = $stream.Read($buffer, 0, 1024)
                        $banner = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $bytesRead)

                        Write-Host "Connected [SSH banner] ✗ FAILED" -ForegroundColor Red

                        # Send fake SSH version
                        $sshVersion = [System.Text.Encoding]::UTF8.GetBytes("SSH-2.0-OpenSSH_7.4`r`n")
                        $stream.Write($sshVersion, 0, $sshVersion.Length)
                    }
                    catch {
                        Write-Host "Connected but error: $_ ✗ FAILED" -ForegroundColor Red
                    }
                }
                else {
                    Write-Host "Connected ✗ FAILED (auth failed)" -ForegroundColor Red
                }

                $tcpClient.Close()
            }
            catch {
                Write-Host "Connection failed ✗ FAILED" -ForegroundColor Red
            }
        }
        else {
            Write-Host "Timeout ✗ FAILED" -ForegroundColor Yellow
            $tcpClient.Close()
        }

        $attemptCount++

    }
    catch {
        Write-Host "Error: $_ ✗ FAILED" -ForegroundColor Red
        $attemptCount++
    }

    # Progress update every 10 attempts
    if ($attempt % 10 -eq 0) {
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        $rate = $attempt / $elapsed
        Write-Host "        Progress: $attempt/$ATTEMPTS attempts ($([math]::Round($rate, 1)) attempts/sec)" -ForegroundColor Gray
    }

    # Delay between attempts
    Start-Sleep -Milliseconds $DELAY
}

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

# Results
Write-Host ""
Write-Host "=" * 70
Write-Host "BRUTE FORCE ATTACK RESULTS" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host "Target:             ${TARGET_IP}:${TARGET_PORT}"
Write-Host "Total Attempts:     $attemptCount"
Write-Host "Duration:           $([math]::Round($duration, 2)) seconds"
Write-Host "Attack Rate:        $([math]::Round($attemptCount / $duration, 2)) attempts/second"
Write-Host "Connections Made:   $connectionAttempts"
Write-Host "Successful Logins:  0 (simulated - all should fail)"

Write-Host ""
Write-Host "=" * 70
Write-Host "EXPECTED IDS/IPS DETECTION" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host "✓ Rule-Based Detection:" -ForegroundColor Green
Write-Host "  - Brute force attack pattern (>20 attempts/min)"
Write-Host "  - Category: BRUTE_FORCE"
Write-Host "  - Severity: CRITICAL"
Write-Host "  - Target Port: $TARGET_PORT"
Write-Host ""
Write-Host "✓ ML Detection:" -ForegroundColor Green
Write-Host "  - High connection rate to single port"
Write-Host "  - Multiple failed authentication patterns"
Write-Host "  - Short-lived connections"
Write-Host "  - Threat Level: HIGH or CRITICAL"
Write-Host ""
Write-Host "✓ Baseline Anomaly:" -ForegroundColor Green
Write-Host "  - Unusual authentication activity"
Write-Host "  - High frequency connections"
Write-Host ""
Write-Host "=" * 70
Write-Host "`nCheck the IDS/IPS 'Network Monitor' tab for detection alerts!" -ForegroundColor Yellow
Write-Host "Expected alert: '🚨 Potential brute force attack'" -ForegroundColor Yellow
Write-Host "=" * 70

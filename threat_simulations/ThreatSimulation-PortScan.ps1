# Threat Simulation 1: Port Scanning Attack (PowerShell)
#
# This script simulates a port scanning attack to test IDS/IPS detection.
# Expected Detection: Port scanning pattern (>100 packets/min to different ports)
#
# ⚠️ WARNING: Only use on networks you own or have permission to test!

# Configuration
$TARGET_IP = "192.168.1.50"  # ⚠️ CHANGE THIS to your IDS/IPS monitored system
$START_PORT = 20
$END_PORT = 1024
$TIMEOUT = 500  # Milliseconds
$SCAN_DELAY = 100  # Milliseconds between port probes

Write-Host "=" * 70
Write-Host "THREAT SIMULATION 1: Port Scanning Attack" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host ""
Write-Host "Target IP:   $TARGET_IP"
Write-Host "Port Range:  $START_PORT-$END_PORT"
Write-Host "Scan Delay:  ${SCAN_DELAY}ms"
Write-Host "Timeout:     ${TIMEOUT}ms"
Write-Host ""
Write-Host "⚠️  WARNING: This simulates a real port scan attack!" -ForegroundColor Yellow
Write-Host "    Only run on networks you own or have permission to test."
Write-Host ""
Write-Host "=" * 70

# Confirmation
$confirmation = Read-Host "`nContinue with port scan simulation? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Simulation cancelled." -ForegroundColor Yellow
    exit
}

Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Starting port scan..."
Write-Host ("-" * 70)

$openPorts = @()
$closedPorts = 0
$filteredPorts = 0
$startTime = Get-Date

# Port scan loop
for ($port = $START_PORT; $port -le $END_PORT; $port++) {
    try {
        # Create TCP client
        $tcpClient = New-Object System.Net.Sockets.TcpClient

        # Attempt connection with timeout
        $connection = $tcpClient.BeginConnect($TARGET_IP, $port, $null, $null)
        $wait = $connection.AsyncWaitHandle.WaitOne($TIMEOUT, $false)

        if (!$wait) {
            # Timeout
            $tcpClient.Close()
            $filteredPorts++
        }
        else {
            # Try to complete connection
            try {
                $tcpClient.EndConnect($connection)

                # Port is open
                $openPorts += $port
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Port $("{0,5}" -f $port): OPEN ✓" -ForegroundColor Green

                # Try to grab banner (for HTTP-like services)
                if ($port -in @(21, 22, 23, 25, 80, 110, 143, 443, 3306, 3389)) {
                    try {
                        $stream = $tcpClient.GetStream()
                        $stream.ReadTimeout = 500

                        # Send basic HTTP request
                        $writer = New-Object System.IO.StreamWriter($stream)
                        $writer.WriteLine("HEAD / HTTP/1.0")
                        $writer.WriteLine("")
                        $writer.Flush()

                        # Try to read banner
                        $reader = New-Object System.IO.StreamReader($stream)
                        $banner = $reader.ReadLine()
                        if ($banner) {
                            Write-Host "                  Banner: $($banner.Substring(0, [Math]::Min(80, $banner.Length)))" -ForegroundColor Gray
                        }
                    }
                    catch {
                        # Banner grab failed, that's okay
                    }
                }

                $tcpClient.Close()
            }
            catch {
                # Connection failed
                $closedPorts++
            }
        }
    }
    catch {
        $closedPorts++
    }

    # Progress indicator every 100 ports
    if ($closedPorts % 100 -eq 0 -and $closedPorts -gt 0) {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Scanned $closedPorts ports..." -ForegroundColor Gray
    }

    # Delay between scans
    Start-Sleep -Milliseconds $SCAN_DELAY
}

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

# Results
Write-Host ""
Write-Host "=" * 70
Write-Host "PORT SCAN RESULTS" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host "Target:          $TARGET_IP"
Write-Host "Ports Scanned:   $START_PORT-$END_PORT ($($END_PORT - $START_PORT + 1) ports)"
Write-Host "Duration:        $([math]::Round($duration, 2)) seconds"
Write-Host "Scan Rate:       $([math]::Round(($END_PORT - $START_PORT + 1) / $duration, 2)) ports/second"
Write-Host ""
Write-Host "Open Ports:      $($openPorts.Count)" -ForegroundColor Green
Write-Host "Closed Ports:    $closedPorts" -ForegroundColor Gray
Write-Host "Filtered Ports:  $filteredPorts" -ForegroundColor Yellow

if ($openPorts.Count -gt 0) {
    $portList = $openPorts[0..[Math]::Min(19, $openPorts.Count - 1)] -join ", "
    Write-Host "`nOpen Ports List: $portList" -ForegroundColor Green
    if ($openPorts.Count -gt 20) {
        Write-Host "                 ... and $($openPorts.Count - 20) more" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=" * 70
Write-Host "EXPECTED IDS/IPS DETECTION" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host "✓ Rule-Based Detection:" -ForegroundColor Green
Write-Host "  - Port scanning pattern (>100 packets/min)"
Write-Host "  - Category: PORT_SCAN"
Write-Host "  - Severity: CRITICAL"
Write-Host ""
Write-Host "✓ ML Detection:" -ForegroundColor Green
Write-Host "  - High packet rate"
Write-Host "  - Multiple connection attempts"
Write-Host "  - No response on closed ports"
Write-Host "  - Threat Level: HIGH or CRITICAL"
Write-Host ""
Write-Host "✓ Baseline Anomaly:" -ForegroundColor Green
Write-Host "  - Unusual traffic pattern"
Write-Host "  - Multiple port connections from single source"
Write-Host ""
Write-Host "=" * 70
Write-Host "`nCheck the IDS/IPS 'Network Monitor' tab for detection alerts!" -ForegroundColor Yellow
Write-Host "=" * 70

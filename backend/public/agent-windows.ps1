# Security Validation Platform - Windows agent
# Copy this exact 2-line command from your dashboard and run it in PowerShell:
#   $env:SVP_API_KEY="YOUR_API_KEY"; irm https://<your-app>.onrender.com/public/agent-windows.ps1 | iex
#
# It scans this machine and reports the results to your dashboard.
# Nothing gets installed - it only uses built-in Windows tools.

$ErrorActionPreference = "Stop"

$BackendUrl = if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "https://security-validation-platform.onrender.com" }
$ApiKey = $env:SVP_API_KEY

if (-not $ApiKey) {
    Write-Host "Missing API key." -ForegroundColor Red
    Write-Host "Copy the exact install command from your dashboard - it already includes your key." -ForegroundColor Red
    exit 1
}

Write-Host "Security Validation Platform - scanning this machine..."
Write-Host ""

$hostnameValue = $env:COMPUTERNAME
try { $ip = (Test-Connection -ComputerName $hostnameValue -Count 1).IPV4Address.IPAddressToString } catch { $ip = "127.0.0.1" }

$firewallStatus = (netsh advfirewall show allprofiles state) -join "`n"
$openPorts      = (netstat -an) -join "`n"
$passwordPolicy = (net accounts) -join "`n"

$rdpRaw = reg query "HKLM\System\CurrentControlSet\Control\Terminal Server" /v fDenyTSConnections 2>$null
$rdpStatus = if ($rdpRaw -match "0x1") { "disabled" } else { "enabled" }

$findings = @()

$fwOn = $firewallStatus.ToLower() -match "state\s+on"
$findings += @{ control_id = "WIN-001"; title = "Windows Firewall enabled"; severity = "critical";
                passed = [bool]$fwOn; detail = if ($fwOn) { "Firewall ON" } else { "Firewall OFF or unknown" } }

$rdpOk = $rdpStatus -eq "disabled"
$findings += @{ control_id = "WIN-002"; title = "RDP access restricted"; severity = "critical";
                passed = $rdpOk; detail = "RDP is $rdpStatus" }

$telnetOpen = $openPorts -match ":23\s"
$findings += @{ control_id = "WIN-003"; title = "Telnet not running"; severity = "critical";
                passed = -not [bool]$telnetOpen; detail = if ($telnetOpen) { "Telnet port 23 detected" } else { "Telnet not detected" } }

$pwdNeverExpires = $passwordPolicy -match "Never"
$findings += @{ control_id = "WIN-004"; title = "Password expiry configured"; severity = "medium";
                passed = -not [bool]$pwdNeverExpires; detail = if ($pwdNeverExpires) { "Password never expires" } else { "Password expiry configured" } }

$total = $findings.Count
$passedCount = ($findings | Where-Object { $_.passed }).Count
$score = if ($total -gt 0) { [math]::Round(($passedCount / $total) * 100, 1) } else { 0 }

Write-Host "--- Scan results ---"
foreach ($f in $findings) {
    $status = if ($f.passed) { "PASS" } else { "FAIL" }
    Write-Host "[$status] $($f.control_id) - $($f.title) ($($f.detail))"
}
Write-Host "Score: $score%"
Write-Host "--------------------"
Write-Host ""

$report = @{
    hostname   = $hostnameValue
    ip_address = $ip
    os_type    = "windows"
    score      = $score
    findings   = $findings
}

Write-Host "Sending results to your dashboard..."

try {
    $submitResponse = Invoke-RestMethod -Uri "$BackendUrl/api/scan" -Method Post `
        -ContentType "application/json" `
        -Headers @{ "X-API-Key" = $ApiKey } `
        -Body ($report | ConvertTo-Json -Depth 5)

    Write-Host "Done! Check your dashboard for the full report." -ForegroundColor Green
}
catch {
    Write-Host "Something went wrong: $_" -ForegroundColor Red
    exit 1
}

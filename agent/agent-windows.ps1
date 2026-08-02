# Security Validation Platform - Windows one-liner agent
#
# Run it with (PowerShell's equivalent of "curl | bash"):
#   irm https://<your-backend>.onrender.com/public/agent-windows.ps1 | iex
#
# Nothing is installed. This uses only built-in Windows tools (netsh, net,
# reg, netstat) and PowerShell's own Invoke-RestMethod - no Python, no
# downloads, no admin install step.

$ErrorActionPreference = "Stop"

$BackendUrl = if ($env:BACKEND_URL) { $env:BACKEND_URL } else { "https://security-validation-platform.onrender.com" }

Write-Host "Security Validation Platform - agent scan"
Write-Host "Backend: $BackendUrl"
Write-Host ""

# --- 1. Login -------------------------------------------------------------
$Username = Read-Host "Platform username"
$SecurePassword = Read-Host "Platform password" -AsSecureString
$Password = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
)

$loginBody = @{ username = $Username; password = $Password } | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$BackendUrl/api/auth/login" `
        -Method Post -ContentType "application/json" -Body $loginBody
}
catch {
    Write-Host "Login failed. Check your username/password and try again." -ForegroundColor Red
    exit 1
}

$Token = $loginResponse.access_token
if (-not $Token) {
    Write-Host "Login did not return a token. Aborting - no scan will run." -ForegroundColor Red
    exit 1
}

Write-Host "Login OK. Running local security checks..." -ForegroundColor Green
Write-Host ""

# --- 2. Collect facts -------------------------------------------------------
$hostname = $env:COMPUTERNAME
try { $ip = (Test-Connection -ComputerName $hostname -Count 1).IPV4Address.IPAddressToString } catch { $ip = "127.0.0.1" }

$firewallStatus = (netsh advfirewall show allprofiles state) -join "`n"
$openPorts      = (netstat -an) -join "`n"
$passwordPolicy = (net accounts) -join "`n"

$rdpRaw = reg query "HKLM\System\CurrentControlSet\Control\Terminal Server" /v fDenyTSConnections 2>$null
$rdpStatus = if ($rdpRaw -match "0x1") { "disabled" } else { "enabled" }

# --- 3. Run checks ----------------------------------------------------------
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
    hostname   = $hostname
    ip_address = $ip
    score      = $score
    findings   = $findings
}

# --- 4. Submit to backend ---------------------------------------------------
Write-Host "Submitting results to $BackendUrl ..."

try {
    $submitResponse = Invoke-RestMethod -Uri "$BackendUrl/api/scan" -Method Post `
        -ContentType "application/json" `
        -Headers @{ Authorization = "Bearer $Token" } `
        -Body ($report | ConvertTo-Json -Depth 5)

    Write-Host ($submitResponse | ConvertTo-Json -Depth 5)
}
catch {
    Write-Host "Failed to submit scan: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Done. View the result on the dashboard." -ForegroundColor Green
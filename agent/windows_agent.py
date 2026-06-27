import json
import time
import requests
import schedule
import socket
import subprocess

BACKEND_URL = "https://security-platform-production.up.railway.app/api/scan"
SCAN_INTERVAL_HOURS = 12

def get_open_ports():
    try:
        result = subprocess.run(["netstat", "-an"], capture_output=True, text=True)
        return result.stdout
    except:
        return ""

def get_firewall_status():
    try:
        result = subprocess.run(
            ["netsh", "advfirewall", "show", "allprofiles", "state"],
            capture_output=True, text=True
        )
        return result.stdout
    except:
        return ""

def get_password_policy():
    try:
        result = subprocess.run(["net", "accounts"], capture_output=True, text=True)
        return result.stdout
    except:
        return ""

def get_rdp_status():
    try:
        result = subprocess.run(
            ["reg", "query",
             "HKLM\\System\\CurrentControlSet\\Control\\Terminal Server",
             "/v", "fDenyTSConnections"],
            capture_output=True, text=True
        )
        return "disabled" if "0x1" in result.stdout else "enabled"
    except:
        return "unknown"

def run_windows_checks(data):
    findings = []

    # Check firewall
    fw = data["firewall_status"].lower()
    findings.append({
        "control_id": "WIN-001",
        "title": "Windows Firewall enabled",
        "severity": "critical",
        "passed": "on" in fw,
        "detail": "Firewall ON" if "on" in fw else "Firewall OFF or unknown"
    })

    # Check RDP
    rdp = data["rdp_status"]
    findings.append({
        "control_id": "WIN-002",
        "title": "RDP access restricted",
        "severity": "critical",
        "passed": rdp == "disabled",
        "detail": f"RDP is {rdp}"
    })

    # Check open ports for Telnet
    findings.append({
        "control_id": "WIN-003",
        "title": "Telnet not running",
        "severity": "critical",
        "passed": ":23 " not in data["open_ports"],
        "detail": "Telnet port 23 detected" if ":23 " in data["open_ports"] else "Telnet not detected"
    })

    # Check password policy
    policy = data["password_policy"]
    findings.append({
        "control_id": "WIN-004",
        "title": "Password expiry configured",
        "severity": "medium",
        "passed": "Never" not in policy,
        "detail": "Password never expires" if "Never" in policy else "Password expiry configured"
    })

    return findings

def calculate_score(findings):
    total = len(findings)
    passed = sum(1 for f in findings if f["passed"])
    return round((passed / total) * 100, 1) if total > 0 else 0

def run_scan():
    print(f"🔍 Running Windows scan...")
    data = {
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "firewall_status": get_firewall_status(),
        "open_ports": get_open_ports(),
        "password_policy": get_password_policy(),
        "rdp_status": get_rdp_status()
    }

    findings = run_windows_checks(data)
    score = calculate_score(findings)

    report = {
        "hostname": data["hostname"],
        "ip_address": data["ip_address"],
        "score": score,
        "findings": findings
    }

    try:
        response = requests.post(BACKEND_URL, json=report, timeout=10)
        response.raise_for_status()
        print(f"✅ Scan sent. Score: {score}%")
    except Exception as e:
        print(f"❌ Failed to send: {e}")
        with open("scan_results.json", "w") as f:
            json.dump(report, f, indent=2)
        print("💾 Saved locally to scan_results.json")

if __name__ == "__main__":
    print(f"🛡️  Windows Security Agent started on {socket.gethostname()}")
    print(f"📡 Reporting to: {BACKEND_URL}")
    print(f"⏰ Scanning every {SCAN_INTERVAL_HOURS} hours\n")

    run_scan()

    schedule.every(SCAN_INTERVAL_HOURS).hours.do(run_scan)

    while True:
        schedule.run_pending()
        time.sleep(60)
#!/usr/bin/env bash
# Security Validation Platform - Linux agent
# Copy this exact command from your dashboard and run it:
#   curl -fsSL https://<your-app>.onrender.com/public/agent-linux.sh | bash -s -- YOUR_API_KEY
#
# It scans this machine and reports the results to your dashboard.
# Nothing gets installed - it only needs bash, python3 and curl.

set -euo pipefail

BACKEND_URL="${BACKEND_URL:-https://security-validation-platform.onrender.com}"
API_KEY="${1:-${SVP_API_KEY:-}}"

if [ -z "$API_KEY" ]; then
  echo "Missing API key."
  echo "Copy the exact install command from your dashboard - it already includes your key."
  exit 1
fi

echo "Security Validation Platform - scanning this machine..."
echo

REPORT_JSON=$(python3 - <<'PYEOF'
import json, socket, subprocess

def get_open_ports():
    try:
        r = subprocess.run(["ss", "-tuln"], capture_output=True, text=True)
        return r.stdout
    except Exception:
        return ""

def get_ssh_config():
    config = {}
    try:
        with open("/etc/ssh/sshd_config") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        config[parts[0]] = parts[1]
    except FileNotFoundError:
        config["error"] = "sshd_config not found"
    return config

def get_password_policy():
    policy = {}
    try:
        with open("/etc/login.defs") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split()
                    if len(parts) == 2:
                        policy[parts[0]] = parts[1]
    except FileNotFoundError:
        policy["error"] = "login.defs not found"
    return policy

def check_ssh_root_login(ssh_config):
    value = ssh_config.get("PermitRootLogin", "yes").lower()
    passed = value in ["no", "prohibit-password"]
    return {"control_id": "SSH-001", "title": "Root login disabled",
            "severity": "critical", "passed": passed,
            "detail": f"PermitRootLogin is set to '{value}'"}

def check_ssh_password_auth(ssh_config):
    value = ssh_config.get("PasswordAuthentication", "yes").lower()
    passed = value == "no"
    return {"control_id": "SSH-002", "title": "SSH password authentication disabled",
            "severity": "medium", "passed": passed,
            "detail": f"PasswordAuthentication is set to '{value}'"}

def check_telnet_running(open_ports):
    passed = "23" not in open_ports
    return {"control_id": "NET-001", "title": "Telnet not running",
            "severity": "critical", "passed": passed,
            "detail": "Telnet port 23 detected" if not passed else "Telnet not detected"}

def check_password_expiry(policy):
    max_days = policy.get("PASS_MAX_DAYS", "99999")
    try:
        passed = int(max_days) <= 90
    except ValueError:
        passed = False
    return {"control_id": "PWD-001", "title": "Password expiry configured (<=90 days)",
            "severity": "medium", "passed": passed,
            "detail": f"PASS_MAX_DAYS is set to {max_days}"}

ssh_config = get_ssh_config()
open_ports = get_open_ports()
password_policy = get_password_policy()

findings = [
    check_ssh_root_login(ssh_config),
    check_ssh_password_auth(ssh_config),
    check_telnet_running(open_ports),
    check_password_expiry(password_policy),
]

total = len(findings)
passed = sum(1 for f in findings if f["passed"])
score = round((passed / total) * 100, 1) if total else 0

report = {
    "hostname": socket.gethostname(),
    "ip_address": socket.gethostbyname(socket.gethostname()),
    "os_type": "linux",
    "score": score,
    "findings": findings,
}

print("--- Scan results ---")
for f in findings:
    status = "PASS" if f["passed"] else "FAIL"
    print(f"[{status}] {f['control_id']} - {f['title']} ({f['detail']})")
print(f"Score: {score}%")
print("--------------------")

json.dump(report, open("/tmp/svp_report.json", "w"))
PYEOF
)

REPORT_JSON=$(cat /tmp/svp_report.json)
rm -f /tmp/svp_report.json

echo
echo "Sending results to your dashboard..."

HTTP_CODE=$(curl -s -o /tmp/svp_resp.json -w "%{http_code}" -X POST "${BACKEND_URL}/api/scan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d "${REPORT_JSON}")

if [ "$HTTP_CODE" = "200" ]; then
  echo "Done! Check your dashboard for the full report."
else
  echo "Something went wrong (HTTP $HTTP_CODE):"
  cat /tmp/svp_resp.json
fi
rm -f /tmp/svp_resp.json

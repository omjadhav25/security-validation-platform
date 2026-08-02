#!/usr/bin/env bash
# Security Validation Platform - Linux one-liner agent
#
# Run it with:
#   curl -fsSL https://<your-backend>.onrender.com/public/agent-linux.sh | bash
#
# It will:
#   1. Ask for your platform username/password (same login as the dashboard)
#   2. Log in to the backend to get a token - the scan is REFUSED without a valid login
#   3. Collect SSH/firewall/password-policy facts from this machine
#   4. Print the results on screen
#   5. Submit them to the backend so they show up on the website
#
# Nothing is installed - it only needs bash, python3 and curl, which almost
# every Linux box already has.

set -euo pipefail

BACKEND_URL="${BACKEND_URL:-https://security-validation-platform.onrender.com}"

echo "Security Validation Platform - agent scan"
echo "Backend: ${BACKEND_URL}"
echo

# --- 1. Login -----------------------------------------------------------
read -rp "Platform username: " SVP_USERNAME
read -rsp "Platform password: " SVP_PASSWORD
echo
echo

LOGIN_RESPONSE=$(curl -fsS -X POST "${BACKEND_URL}/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${SVP_USERNAME}\",\"password\":\"${SVP_PASSWORD}\"}") || {
    echo "Login failed. Check your username/password and try again."
    exit 1
  }

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$TOKEN" ]; then
  echo "Login did not return a token. Aborting - no scan will run."
  exit 1
fi

echo "Login OK. Running local security checks..."
echo

# --- 2. Collect facts + run checks + print + build report --------------
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
    "score": score,
    "findings": findings,
}

print("--- Scan results ---")
for f in findings:
    status = "PASS" if f["passed"] else "FAIL"
    print(f"[{status}] {f['control_id']} - {f['title']} ({f['detail']})")
print(f"Score: {score}%")
print("--------------------")

import sys
json.dump(report, open("/tmp/svp_report.json", "w"))
PYEOF
)

REPORT_JSON=$(cat /tmp/svp_report.json)
rm -f /tmp/svp_report.json

# --- 3. Submit to backend -------------------------------------------------
echo
echo "Submitting results to ${BACKEND_URL} ..."

curl -fsS -X POST "${BACKEND_URL}/api/scan" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d "${REPORT_JSON}" | python3 -m json.tool

echo
echo "Done. View the result on the dashboard."
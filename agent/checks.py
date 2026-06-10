def check_ssh_root_login(ssh_config):
    value = ssh_config.get("PermitRootLogin", "yes").lower()
    passed = value in ["no", "prohibit-password"]
    return {
        "control_id": "SSH-001",
        "title": "Root login disabled",
        "severity": "critical",
        "passed": passed,
        "detail": f"PermitRootLogin is set to '{value}'"
    }

def check_ssh_password_auth(ssh_config):
    value = ssh_config.get("PasswordAuthentication", "yes").lower()
    passed = value == "no"
    return {
        "control_id": "SSH-002",
        "title": "SSH password authentication disabled",
        "severity": "medium",
        "passed": passed,
        "detail": f"PasswordAuthentication is set to '{value}'"
    }

def check_ssh_banner(ssh_config):
    value = ssh_config.get("Banner", "none")
    passed = value.lower() != "none"
    return {
        "control_id": "SSH-003",
        "title": "SSH login banner configured",
        "severity": "low",
        "passed": passed,
        "detail": f"Banner is set to '{value}'"
    }

def check_telnet_running(open_ports):
    passed = "23" not in open_ports
    return {
        "control_id": "NET-001",
        "title": "Telnet not running",
        "severity": "critical",
        "passed": passed,
        "detail": "Telnet port 23 detected" if not passed else "Telnet not detected"
    }

def check_ftp_running(open_ports):
    passed = ":21 " not in open_ports
    return {
        "control_id": "NET-002",
        "title": "FTP not running",
        "severity": "medium",
        "passed": passed,
        "detail": "FTP port 21 detected" if not passed else "FTP not detected"
    }

def check_password_expiry(password_policy):
    max_days = password_policy.get("PASS_MAX_DAYS", "99999")
    try:
        passed = int(max_days) <= 90
    except ValueError:
        passed = False
    return {
        "control_id": "PWD-001",
        "title": "Password expiry configured (≤90 days)",
        "severity": "medium",
        "passed": passed,
        "detail": f"PASS_MAX_DAYS is set to {max_days}"
    }

def check_password_min_length(password_policy):
    min_len = password_policy.get("PASS_MIN_LEN", "0")
    try:
        passed = int(min_len) >= 12
    except ValueError:
        passed = False
    return {
        "control_id": "PWD-002",
        "title": "Minimum password length ≥ 12",
        "severity": "medium",
        "passed": passed,
        "detail": f"PASS_MIN_LEN is set to {min_len}"
    }

def run_all_checks(data):
    findings = []
    findings.append(check_ssh_root_login(data["ssh_config"]))
    findings.append(check_ssh_password_auth(data["ssh_config"]))
    findings.append(check_ssh_banner(data["ssh_config"]))
    findings.append(check_telnet_running(data["open_ports"]))
    findings.append(check_ftp_running(data["open_ports"]))
    findings.append(check_password_expiry(data["password_policy"]))
    findings.append(check_password_min_length(data["password_policy"]))
    return findings
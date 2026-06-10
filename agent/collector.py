import subprocess
import socket
import os

def get_hostname():
    return socket.gethostname()

def get_ip_address():
    return socket.gethostbyname(socket.gethostname())

def get_open_ports():
    try:
        result = subprocess.run(
            ["ss", "-tuln"],
            capture_output=True, text=True
        )
        return result.stdout
    except Exception as e:
        return str(e)

def get_ssh_config():
    config = {}
    ssh_config_path = "/etc/ssh/sshd_config"
    try:
        with open(ssh_config_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        config[parts[0]] = parts[1]
    except FileNotFoundError:
        config["error"] = "sshd_config not found"
    return config

def get_firewall_rules():
    try:
        result = subprocess.run(
            ["iptables", "-L", "-n"],
            capture_output=True, text=True
        )
        return result.stdout
    except Exception as e:
        return str(e)

def get_user_accounts():
    users = []
    try:
        with open("/etc/passwd", "r") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) >= 7:
                    users.append({
                        "username": parts[0],
                        "uid": parts[2],
                        "gid": parts[3],
                        "home": parts[5],
                        "shell": parts[6]
                    })
    except Exception as e:
        users = [{"error": str(e)}]
    return users

def get_password_policy():
    policy = {}
    try:
        with open("/etc/login.defs", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split()
                    if len(parts) == 2:
                        policy[parts[0]] = parts[1]
    except FileNotFoundError:
        policy["error"] = "login.defs not found"
    return policy

def get_sudo_users():
    sudo_users = []
    try:
        result = subprocess.run(
            ["getent", "group", "sudo"],
            capture_output=True, text=True
        )
        line = result.stdout.strip()
        if line:
            parts = line.split(":")
            if len(parts) == 4 and parts[3]:
                sudo_users = parts[3].split(",")
    except Exception as e:
        sudo_users = [str(e)]
    return sudo_users

def collect_all():
    return {
        "hostname": get_hostname(),
        "ip_address": get_ip_address(),
        "open_ports": get_open_ports(),
        "ssh_config": get_ssh_config(),
        "firewall_rules": get_firewall_rules(),
        "user_accounts": get_user_accounts(),
        "password_policy": get_password_policy(),
        "sudo_users": get_sudo_users()
    }
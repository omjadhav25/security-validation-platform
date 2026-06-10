import paramiko
import json

CHECKS_SCRIPT = """
import subprocess, socket, json

def get_open_ports():
    try:
        r = subprocess.run(["ss", "-tuln"], capture_output=True, text=True)
        return r.stdout
    except:
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
    except:
        config["error"] = "not found"
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
    except:
        policy["error"] = "not found"
    return policy

data = {
    "hostname": socket.gethostname(),
    "ip_address": socket.gethostbyname(socket.gethostname()),
    "open_ports": get_open_ports(),
    "ssh_config": get_ssh_config(),
    "firewall_rules": "",
    "user_accounts": [],
    "password_policy": get_password_policy(),
    "sudo_users": []
}
print(json.dumps(data))
"""

def scan_remote_server(hostname, username, password=None, key_path=None, port=22):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if key_path:
            client.connect(hostname, port=port, username=username, key_filename=key_path)
        else:
            client.connect(hostname, port=port, username=username, password=password)

        print(f"✅ Connected to {hostname}")

        command = f'python3 -c "{CHECKS_SCRIPT.strip()}"'
        stdin, stdout, stderr = client.exec_command(f"python3 << 'EOF'\n{CHECKS_SCRIPT}\nEOF")

        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if error:
            print(f"⚠️  Remote stderr: {error}")

        data = json.loads(output)
        return data

    except paramiko.AuthenticationException:
        print(f"❌ Authentication failed for {hostname}")
        return None
    except paramiko.SSHException as e:
        print(f"❌ SSH error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        client.close()


if __name__ == "__main__":
    # Example usage — replace with your server details
    data = scan_remote_server(
        hostname="192.168.0.xxx",
        username="your-username",
        password="your-password",
    )

    if data:
        print(f"\n✅ Scanned: {data['hostname']}")
        print(json.dumps(data, indent=2))
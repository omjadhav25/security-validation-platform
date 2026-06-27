import json
import threading
import requests
import time
from datetime import datetime
from remote_scanner import scan_remote_server
from checks import run_all_checks
from email_alerts import send_alert

BACKEND_URL = "https://security-platform-production.up.railway.app/api/scan"

def load_targets():
    with open("targets.json") as f:
        return json.load(f)["targets"]

def calculate_score(findings):
    total = len(findings)
    passed = sum(1 for f in findings if f["passed"])
    return round((passed / total) * 100, 1) if total > 0 else 0

def send_to_backend(report):
    try:
        response = requests.post(BACKEND_URL, json=report, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"   ❌ Failed to send to backend: {e}")
        return False

def scan_linux_ssh(target, results, lock):
    hostname = target["hostname"]
    print(f"🔍 [{hostname}] Starting SSH scan...")

    data = scan_remote_server(
        hostname=hostname,
        username=target["username"],
        password=target.get("password"),
        key_path=target.get("key_path"),
        port=target.get("port", 22)
    )

    if not data:
        with lock:
            results.append({
                "target": hostname,
                "status": "failed",
                "error": "SSH connection failed"
            })
        return

    findings = run_all_checks(data)
    score = calculate_score(findings)

    report = {
        "hostname": data["hostname"],
        "ip_address": data["ip_address"],
        "score": score,
        "findings": findings
    }

    success = send_to_backend(report)
    send_alert(report)

    with lock:
        results.append({
            "target": hostname,
            "status": "success" if success else "sent_failed",
            "score": score,
            "hostname": data["hostname"]
        })

    print(f"✅ [{hostname}] Done — Score: {score}%")

def scan_local(target, results, lock):
    print(f"🔍 [localhost] Starting local scan...")

    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))

    from collector import collect_all
    data = collect_all()
    findings = run_all_checks(data)
    score = calculate_score(findings)

    report = {
        "hostname": data["hostname"],
        "ip_address": data["ip_address"],
        "score": score,
        "findings": findings
    }

    success = send_to_backend(report)
    send_alert(report)

    with lock:
        results.append({
            "target": "localhost",
            "status": "success" if success else "sent_failed",
            "score": score,
            "hostname": data["hostname"]
        })

    print(f"✅ [localhost] Done — Score: {score}%")

def scan_target(target, results, lock):
    try:
        method = target.get("method", "ssh")

        if method == "local":
            scan_local(target, results, lock)
        elif method == "ssh":
            scan_linux_ssh(target, results, lock)
        elif method == "agent":
            print(f"⏭️  [{target['hostname']}] Agent-based — skipping (agent reports on its own)")
            with lock:
                results.append({
                    "target": target["hostname"],
                    "status": "agent_based",
                    "note": "Agent reports independently"
                })
    except Exception as e:
        print(f"❌ [{target.get('hostname')}] Error: {e}")
        with lock:
            results.append({
                "target": target.get("hostname"),
                "status": "error",
                "error": str(e)
            })

def run_all_scans():
    targets = load_targets()
    results = []
    lock = threading.Lock()
    threads = []

    print(f"\n{'='*50}")
    print(f"🛡️  Security Validation Platform")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Scanning {len(targets)} targets concurrently")
    print(f"{'='*50}\n")

    start_time = time.time()

    # Launch one thread per target — concurrent scanning
    for target in targets:
        t = threading.Thread(
            target=scan_target,
            args=(target, results, lock)
        )
        threads.append(t)
        t.start()

    # Wait for all scans to finish
    for t in threads:
        t.join()

    elapsed = round(time.time() - start_time, 1)

    print(f"\n{'='*50}")
    print(f"📊 SCAN SUMMARY ({elapsed}s)")
    print(f"{'='*50}")

    for r in results:
        if r["status"] == "success":
            score = r.get("score", 0)
            color = "✅" if score >= 80 else "⚠️ " if score >= 50 else "🚨"
            print(f"{color} {r['target']:30} Score: {score}%")
        elif r["status"] == "failed":
            print(f"❌ {r['target']:30} FAILED: {r.get('error')}")
        elif r["status"] == "agent_based":
            print(f"📡 {r['target']:30} Agent-based (reports independently)")
        else:
            print(f"⚠️  {r['target']:30} {r['status']}")

    print(f"{'='*50}\n")
    return results

if __name__ == "__main__":
    run_all_scans()
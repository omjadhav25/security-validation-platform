import json
import requests
from collector import collect_all
from checks import run_all_checks

BACKEND_URL = "http://localhost:8000/api/scan"

def calculate_score(findings):
    total = len(findings)
    passed = sum(1 for f in findings if f["passed"])
    return round((passed / total) * 100, 1) if total > 0 else 0

def build_report(data, findings):
    return {
        "hostname": data["hostname"],
        "ip_address": data["ip_address"],
        "score": calculate_score(findings),
        "findings": findings
    }

def send_report(report):
    try:
        response = requests.post(BACKEND_URL, json=report)
        response.raise_for_status()
        print(f"✅ Report sent successfully. Score: {report['score']}%")
    except requests.exceptions.ConnectionError:
        print("⚠️  Backend not running. Printing report locally:\n")
        print(json.dumps(report, indent=2))

if __name__ == "__main__":
    print("🔍 Collecting system data...")
    data = collect_all()

    print("🔎 Running security checks...")
    findings = run_all_checks(data)

    report = build_report(data, findings)
    send_report(report)
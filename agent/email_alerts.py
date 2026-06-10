import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SENDER = os.getenv("EMAIL_SENDER")
PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT = os.getenv("EMAIL_RECIPIENT")

def build_html_email(report):
    critical_findings = [
        f for f in report["findings"]
        if f["severity"] == "critical" and not f["passed"]
    ]

    score = report["score"]
    score_color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 50 else "#ef4444"

    critical_rows = ""
    for f in critical_findings:
        critical_rows += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #fee2e2;font-family:monospace;color:#6b7280">{f['control_id']}</td>
            <td style="padding:8px;border-bottom:1px solid #fee2e2;color:#111827">{f['title']}</td>
            <td style="padding:8px;border-bottom:1px solid #fee2e2;color:#374151">{f['detail']}</td>
        </tr>
        """

    html = f"""
    <html>
    <body style="font-family:Arial,sans-serif;background:#f9fafb;padding:24px">
        <div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;border:1px solid #e5e7eb">

            <!-- Header -->
            <div style="background:#1e3a5f;padding:24px;text-align:center">
                <h1 style="color:white;margin:0;font-size:20px">🔒 Security Alert</h1>
                <p style="color:#93c5fd;margin:8px 0 0">Security Validation Platform</p>
            </div>

            <!-- Score -->
            <div style="padding:24px;text-align:center;border-bottom:1px solid #e5e7eb">
                <p style="color:#6b7280;margin:0 0 8px">Compliance Score for <strong>{report['hostname']}</strong></p>
                <div style="font-size:48px;font-weight:bold;color:{score_color}">{score}%</div>
                <p style="color:#ef4444;font-weight:bold;margin:8px 0 0">
                    ⚠️ {len(critical_findings)} Critical {"Issue" if len(critical_findings) == 1 else "Issues"} Found
                </p>
            </div>

            <!-- Critical Findings -->
            <div style="padding:24px">
                <h2 style="color:#1e3a5f;font-size:16px;margin:0 0 16px">Critical Findings Requiring Immediate Action</h2>
                <table style="width:100%;border-collapse:collapse;font-size:13px">
                    <thead>
                        <tr style="background:#fef2f2">
                            <th style="padding:8px;text-align:left;color:#991b1b;font-size:11px;text-transform:uppercase">Control</th>
                            <th style="padding:8px;text-align:left;color:#991b1b;font-size:11px;text-transform:uppercase">Issue</th>
                            <th style="padding:8px;text-align:left;color:#991b1b;font-size:11px;text-transform:uppercase">Detail</th>
                        </tr>
                    </thead>
                    <tbody>
                        {critical_rows if critical_rows else '<tr><td colspan="3" style="padding:16px;text-align:center;color:#22c55e">No critical issues found</td></tr>'}
                    </tbody>
                </table>
            </div>

            <!-- Footer -->
            <div style="background:#f9fafb;padding:16px;text-align:center;border-top:1px solid #e5e7eb">
                <p style="color:#9ca3af;font-size:12px;margin:0">
                    Security Validation Platform — Automated Alert
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def send_alert(report):
    critical_count = sum(
        1 for f in report["findings"]
        if f["severity"] == "critical" and not f["passed"]
    )

    if critical_count == 0:
        print("✅ No critical findings — no alert sent")
        return

    if not SENDER or not PASSWORD or not RECIPIENT:
        print("⚠️  Email not configured — skipping alert")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚨 Security Alert: {report['hostname']} — Score {report['score']}% ({critical_count} Critical)"
    msg["From"] = SENDER
    msg["To"] = RECIPIENT

    html_content = build_html_email(report)
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER, PASSWORD)
            server.sendmail(SENDER, RECIPIENT, msg.as_string())
        print(f"📧 Alert email sent to {RECIPIENT}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
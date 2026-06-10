from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime

SEVERITY_COLORS = {
    "critical": colors.HexColor("#ef4444"),
    "medium": colors.HexColor("#f59e0b"),
    "low": colors.HexColor("#3b82f6"),
}

STATUS_COLORS = {
    True: colors.HexColor("#22c55e"),
    False: colors.HexColor("#ef4444"),
}

def generate_pdf_report(server, scan):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=22,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1e3a5f"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica",
        textColor=colors.HexColor("#6b7280"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontSize=13,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1e3a5f"),
        spaceBefore=16,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica",
        textColor=colors.HexColor("#374151"),
    )

    elements = []

    # Header
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Security Validation Platform", title_style))
    elements.append(Paragraph("CIS Benchmark Compliance Report", subtitle_style))
    elements.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e3a5f")))
    elements.append(Spacer(1, 0.2 * inch))

    # Server info
    elements.append(Paragraph("Server Information", section_style))
    server_data = [
        ["Hostname", server.hostname],
        ["IP Address", server.ip_address],
        ["Scan Date", scan.scanned_at.strftime("%Y-%m-%d %H:%M UTC")],
        ["Compliance Score", f"{scan.score}%"],
    ]
    server_table = Table(server_data, colWidths=[2 * inch, 4.5 * inch])
    server_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1e3a5f")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUND", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    elements.append(server_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Score summary
    findings = scan.findings
    total = len(findings)
    passed = sum(1 for f in findings if f.passed)
    failed = total - passed
    critical = sum(1 for f in findings if f.severity == "critical" and not f.passed)
    medium = sum(1 for f in findings if f.severity == "medium" and not f.passed)
    low = sum(1 for f in findings if f.severity == "low" and not f.passed)

    elements.append(Paragraph("Compliance Summary", section_style))
    summary_data = [
        ["Metric", "Value"],
        ["Total Checks", str(total)],
        ["Passed", str(passed)],
        ["Failed", str(failed)],
        ["Critical Failures", str(critical)],
        ["Medium Failures", str(medium)],
        ["Low Failures", str(low)],
    ]
    summary_table = Table(summary_data, colWidths=[3 * inch, 3.5 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Findings
    elements.append(Paragraph("Detailed Findings", section_style))
    findings_data = [["Control ID", "Title", "Severity", "Status", "Detail"]]

    severity_order = {"critical": 0, "medium": 1, "low": 2}
    sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.severity, 3))

    for f in sorted_findings:
        findings_data.append([
            f.control_id,
            Paragraph(f.title, normal_style),
            f.severity.upper(),
            "PASS" if f.passed else "FAIL",
            Paragraph(f.detail, normal_style),
        ])

    findings_table = Table(
        findings_data,
        colWidths=[0.9 * inch, 1.6 * inch, 0.8 * inch, 0.6 * inch, 2.6 * inch]
    )

    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
    ]

    for i, f in enumerate(sorted_findings, start=1):
        sev_color = SEVERITY_COLORS.get(f.severity, colors.gray)
        status_color = STATUS_COLORS.get(f.passed, colors.gray)
        table_style.append(("TEXTCOLOR", (2, i), (2, i), sev_color))
        table_style.append(("TEXTCOLOR", (3, i), (3, i), status_color))
        table_style.append(("FONTNAME", (2, i), (3, i), "Helvetica-Bold"))

    findings_table.setStyle(TableStyle(table_style))
    elements.append(findings_table)

    # Footer
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(
        "Generated by Security Validation Platform — Confidential",
        subtitle_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
"""
Generates downloadable compliance reports (CSV and PDF) from scan history.

These are service functions: the routes in routes/reports.py call them and stream the
returned in-memory file to the browser. Both formats render cleanly with zero scans.
"""

import csv
import io
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.database import db
from app.utils.helpers import iso

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


async def fetch_scan_results(image: str | None = None, limit: int = 500) -> list[dict]:
    """Recent scans, newest first, optionally for one image.

    The (potentially huge) vulnerability list is excluded; the stored severity counts are enough.
    """
    query = {"image": image} if image else {}
    cursor = db.scan_results.find(query, {"vulnerabilities": 0}).sort("scanned_at", -1).limit(limit)
    return [doc async for doc in cursor]


def _scan_rows(scans: list[dict]) -> list[dict]:
    """Flatten scan documents into the rows both report formats share."""
    rows = []
    for scan in scans:
        counts = scan.get("severity_counts", {})
        scanned_at = iso(scan.get("scanned_at")) or ""
        rows.append({
            "id": str(scan.get("_id", "")),
            "image": scan.get("image", "unknown"),
            "scanned_at": scanned_at.replace("T", " ")[:19],
            "scanned_by": scan.get("user_email", "unknown"),
            "risk_score": scan.get("risk_score", 0),
            **{sev: counts.get(sev, 0) for sev in SEVERITIES},
            "total": sum(counts.get(sev, 0) for sev in SEVERITIES),
        })
    return rows


async def generate_csv_report(image: str | None = None) -> io.BytesIO:
    """Build a CSV report and return it as an in-memory file."""
    rows = _scan_rows(await fetch_scan_results(image))

    text = io.StringIO()
    writer = csv.writer(text)
    writer.writerow(["Scan ID", "Image", "Scanned At (UTC)", "Scanned By", "Risk Score",
                     "Critical", "High", "Medium", "Low", "Total"])
    for r in rows:
        writer.writerow([r["id"], r["image"], r["scanned_at"], r["scanned_by"], r["risk_score"],
                         r["CRITICAL"], r["HIGH"], r["MEDIUM"], r["LOW"], r["total"]])
    if not rows:
        writer.writerow(["No scans recorded yet"])

    buffer = io.BytesIO(text.getvalue().encode("utf-8"))
    buffer.seek(0)
    return buffer


async def generate_pdf_report(image: str | None = None) -> io.BytesIO:
    """Build a formatted PDF report and return it as an in-memory file."""
    rows = _scan_rows(await fetch_scan_results(image))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
                            leftMargin=1.8 * cm, rightMargin=1.8 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleNavy", parent=styles["Title"], textColor=colors.HexColor("#1B3A6B"))
    muted_style = ParagraphStyle("Muted", parent=styles["Normal"], textColor=colors.HexColor("#677488"))

    elements = [
        Paragraph("AegisCloud — Security Scan Report", title_style),
        Paragraph(f"Generated {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}", muted_style),
        Spacer(1, 0.8 * cm),
    ]
    if image:
        # Paragraph parses XML-like markup, so user-supplied text must be escaped.
        elements += [Paragraph(f"Filtered to image: <b>{escape(image)}</b>", styles["Normal"]), Spacer(1, 0.4 * cm)]

    totals = {sev: sum(r[sev] for r in rows) for sev in SEVERITIES}
    summary = Table(
        [["Critical", "High", "Medium", "Low", "Scans"],
         [totals["CRITICAL"], totals["HIGH"], totals["MEDIUM"], totals["LOW"], len(rows)]],
        hAlign="LEFT")
    summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B3A6B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E6ED")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements += [summary, Spacer(1, 1 * cm)]

    if rows:
        data = [["Image", "Scanned (UTC)", "By", "Risk", "Crit", "High", "Med", "Low"]]
        for r in rows:
            data.append([r["image"], r["scanned_at"], r["scanned_by"], r["risk_score"],
                         r["CRITICAL"], r["HIGH"], r["MEDIUM"], r["LOW"]])
        detail = Table(data, hAlign="LEFT", repeatRows=1)
        detail.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E86AB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FA")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E6ED")),
            ("ALIGN", (3, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(detail)
    else:
        elements.append(Paragraph("No scans have been recorded yet.", muted_style))

    elements += [Spacer(1, 1 * cm), Paragraph("Confidential — generated by AegisCloud", muted_style)]
    doc.build(elements)
    buffer.seek(0)
    return buffer
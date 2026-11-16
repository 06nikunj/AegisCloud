"""Small shared helpers: time, audit logging, severity maths and input validation."""

import math
import re
from datetime import datetime, timezone

from fastapi import Request

from app.database import db

# Weight of one vulnerability of each severity when scoring risk.
SEVERITY_WEIGHTS = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1}

# Controls how quickly the risk score approaches 100 (see compute_risk_score).
RISK_SCALE = 120.0

# A Docker image reference: letters/digits first, then letters, digits and . _ - / : @
# Starting with a letter or digit stops values like "--config=..." being read as Trivy flags.
IMAGE_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-/:@]{0,199}$")


def utcnow() -> datetime:
    """Current time as a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def iso(value: datetime | None) -> str | None:
    """ISO-8601 string that always carries a UTC offset, even for naive datetimes from MongoDB."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


async def log_audit(action: str, request: Request | None = None,
                    user_email: str | None = None, details: dict | None = None) -> None:
    """Write one entry to the audit trail.

    Never raises: failing to write an audit row must not break the user's request.
    """
    try:
        await db.audit_logs.insert_one({
            "action": action,
            "user_email": user_email,
            "ip": request.client.host if request and request.client else None,
            "details": details or {},
            "timestamp": utcnow(),
        })
    except Exception:
        pass


def count_by_severity(vulnerabilities: list[dict]) -> dict:
    """Tally a Trivy-style vulnerability list into {CRITICAL, HIGH, MEDIUM, LOW} counts."""
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for vuln in vulnerabilities or []:
        severity = str(vuln.get("Severity", "")).upper()
        if severity in counts:
            counts[severity] += 1
    return counts


def compute_risk_score(severity_counts: dict) -> int:
    """Turn severity counts into a 0-100 risk score.

    Each finding adds a weighted amount (Critical 10, High 5, Medium 2, Low 1). The
    total is then squashed with 100 * (1 - e^(-total / 120)), so:
      * a clean image scores 0,
      * every extra finding raises the score,
      * the score approaches but never hits 100, so a bad image and a terrible
        image can still be told apart (a plain capped sum maxes out immediately).
    This is an explainable heuristic for a dashboard, not an industry standard.
    """
    total = sum(SEVERITY_WEIGHTS.get(sev, 0) * count for sev, count in severity_counts.items())
    return max(0, min(100, round(100 * (1 - math.exp(-total / RISK_SCALE)))))


def validate_image_ref(image: str) -> str:
    """Return the trimmed image reference, or raise ValueError with a user-friendly message."""
    cleaned = (image or "").strip()
    if not IMAGE_REF_PATTERN.match(cleaned):
        raise ValueError("That doesn't look like a Docker image name. Use something like nginx:latest.")
    return cleaned


async def latest_severity_totals() -> dict:
    """Severity totals using only the most recent scan of each image.

    Re-scanning the same image therefore replaces its numbers instead of adding to them,
    so the dashboard reflects current posture rather than scan history.
    """
    latest: dict[str, dict] = {}
    cursor = db.scan_results.find({}, {"image": 1, "severity_counts": 1}).sort("scanned_at", -1)
    async for scan in cursor:
        latest.setdefault(scan["image"], scan.get("severity_counts", {}))

    totals = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for counts in latest.values():
        for severity in totals:
            totals[severity] += counts.get(severity, 0)
    return totals
"""
Turns raw Falco webhook events into AegisCloud alert documents.

Falco reports priorities as Emergency / Alert / Critical / Error / Warning / Notice /
Informational / Debug. The UI uses four levels (critical / high / medium / low), so
they are mapped here.
"""

import re
from datetime import datetime

from app.config import settings
from app.models.alert import FalcoEvent
from app.utils.helpers import utcnow

PRIORITY_MAP = {
    "emergency": "critical",
    "alert": "critical",
    "critical": "critical",
    "error": "high",
    "high": "high",
    "warning": "medium",
    "medium": "medium",
    "notice": "low",
    "informational": "low",
    "debug": "low",
    "low": "low",
}

# Falco timestamps carry nanoseconds ("...30.123456789Z"); Python only keeps microseconds.
_TIME_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:?\d{2})?$"
)


def map_priority(raw: str) -> str:
    """Map a Falco priority to critical / high / medium / low (unknown values become low)."""
    return PRIORITY_MAP.get((raw or "").strip().lower(), "low")


def parse_event_time(value: str | None) -> datetime:
    """Parse Falco's timestamp into an aware UTC datetime; falls back to 'now' if unparseable."""
    if not value:
        return utcnow()
    match = _TIME_RE.match(value.strip())
    if not match:
        return utcnow()
    base, fraction, zone = match.groups()
    fraction = (fraction or "0")[:6].ljust(6, "0")
    if zone is None or zone == "Z":
        zone = "+00:00"
    elif ":" not in zone:
        zone = zone[:3] + ":" + zone[3:]
    try:
        return datetime.fromisoformat(f"{base}.{fraction}{zone}")
    except ValueError:
        return utcnow()


def build_alert(event: FalcoEvent, simulated: bool = False) -> dict:
    """Normalise a Falco event into the document stored in the `alerts` collection."""
    fields = event.output_fields or {}
    container = str(fields.get("container.name") or "").strip()
    if container in ("", "<NA>"):
        container = "host"
    return {
        "rule": event.rule.strip(),
        "priority": map_priority(event.priority),
        "falco_priority": event.priority,
        "container_name": container,
        "container_id": str(fields.get("container.id") or ""),
        "command": str(fields.get("proc.cmdline") or "")[:500],
        "output": event.output,
        "hostname": event.hostname,
        "tags": event.tags,
        "acknowledged": False,
        "simulated": simulated,
        "detected_at": parse_event_time(event.time),
    }


def should_notify(priority: str) -> bool:
    """True if alerts of this priority should trigger an SNS notification."""
    return priority in settings.sns_priorities
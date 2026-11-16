"""Prometheus metrics exposed at GET /metrics."""

from prometheus_client import Counter, Gauge, Histogram

from app.database import db
from app.utils.helpers import latest_severity_totals

HTTP_REQUESTS = Counter(
    "aegis_http_requests_total", "HTTP requests handled", ["method", "path", "status"])
HTTP_LATENCY = Histogram(
    "aegis_http_request_duration_seconds", "HTTP request latency in seconds", ["method", "path"])
SCANS_TOTAL = Counter(
    "aegis_scans_total", "Image scans attempted", ["result"])
ALERTS_RECEIVED = Counter(
    "aegis_alerts_received_total", "Runtime alerts received from Falco", ["priority"])
NOTIFICATIONS_SENT = Counter(
    "aegis_notifications_total", "SNS notifications triggered", ["kind"])

OPEN_ALERTS = Gauge("aegis_open_alerts", "Alerts not yet acknowledged")
IMAGES_SCANNED = Gauge("aegis_images_scanned", "Distinct images that have been scanned")
VULNERABILITIES = Gauge(
    "aegis_vulnerabilities", "Vulnerabilities in the latest scan of each image", ["severity"])


async def refresh_gauges() -> None:
    """Update the database-backed gauges just before Prometheus scrapes them."""
    OPEN_ALERTS.set(await db.alerts.count_documents({"acknowledged": False}))
    IMAGES_SCANNED.set(len(await db.scan_results.distinct("image")))
    for severity, count in (await latest_severity_totals()).items():
        VULNERABILITIES.labels(severity=severity.lower()).set(count)
"""
AWS SNS notifications (email / SMS) for critical findings.

Sending never raises: a notification failure is logged and reported as False so it
can never break the request that triggered it. Call these functions from a FastAPI
BackgroundTask so the user isn't kept waiting on AWS.
"""

import asyncio
import logging
import re
from functools import lru_cache

from app.config import settings

logger = logging.getLogger("aegiscloud.sns")


def is_configured() -> bool:
    """True if an SNS topic ARN has been set."""
    return bool(settings.AWS_SNS_TOPIC_ARN)


@lru_cache(maxsize=1)
def _client():
    """Create (once) the boto3 SNS client. Falls back to the AWS CLI credential chain if no keys are set."""
    import boto3

    kwargs = {"region_name": settings.AWS_REGION}
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    return boto3.client("sns", **kwargs)


def _clean_subject(subject: str) -> str:
    """SNS subjects must be a single line of at most 100 characters."""
    return re.sub(r"\s+", " ", subject).strip()[:100]


def _publish(subject: str, message: str) -> None:
    _client().publish(TopicArn=settings.AWS_SNS_TOPIC_ARN, Subject=subject, Message=message)


async def send_alert(subject: str, message: str) -> bool:
    """Publish a notification. Returns True if SNS accepted it, False if skipped or failed."""
    if not is_configured():
        return False
    try:
        await asyncio.to_thread(_publish, _clean_subject(subject), message)
        return True
    except Exception:  # boto3 raises many exception types; none may escape a background task
        logger.warning("SNS notification failed", exc_info=True)
        return False


def format_alert_message(alert: dict) -> tuple[str, str]:
    """Build (subject, body) for a runtime alert."""
    subject = f"[AegisCloud] {alert['priority'].upper()} runtime alert: {alert['rule']}"
    body = (
        f"Priority: {alert['priority'].upper()}\n"
        f"Rule: {alert['rule']}\n"
        f"Container: {alert['container_name']}\n"
        f"Command: {alert.get('command') or 'n/a'}\n\n"
        f"{alert.get('output', '')}\n\n"
        "Review and acknowledge this alert in the AegisCloud dashboard."
    )
    return subject, body


def format_scan_message(image: str, counts: dict, risk_score: int) -> tuple[str, str]:
    """Build (subject, body) for a scan that found critical vulnerabilities."""
    subject = f"[AegisCloud] {counts['CRITICAL']} critical vulnerabilities in {image}"
    body = (
        f"Image: {image}\n"
        f"Risk score: {risk_score}/100\n"
        f"Critical: {counts['CRITICAL']}  High: {counts['HIGH']}  "
        f"Medium: {counts['MEDIUM']}  Low: {counts['LOW']}\n\n"
        "Open the scan in the AegisCloud dashboard to see every CVE and its fix version."
    )
    return subject, body
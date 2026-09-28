from datetime import datetime, timezone

from fastapi import Request

from app.database import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def log_audit(action: str, request: Request | None = None,
                    user_email: str | None = None, details: dict | None = None) -> None:
    """Write one entry to the audit trail. Never lets a logging failure break a request."""
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
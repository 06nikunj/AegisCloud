"""Schema of one audit-trail entry (stored in the `audit_logs` collection)."""

from datetime import datetime

from pydantic import BaseModel


class AuditLog(BaseModel):
    action: str            # e.g. "auth.login", "scan.completed", "alerts.acknowledged"
    user_email: str | None = None
    ip: str | None = None
    details: dict = {}
    timestamp: datetime
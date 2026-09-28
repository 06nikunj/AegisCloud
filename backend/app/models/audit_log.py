from datetime import datetime

from pydantic import BaseModel


class AuditLog(BaseModel):
    action: str            # e.g. "auth.login", "auth.register", "auth.login_failed"
    user_email: str | None = None
    ip: str | None = None
    details: dict = {}
    timestamp: datetime
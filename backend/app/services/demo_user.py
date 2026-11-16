"""Creates or updates the single allowed account at startup."""

import bcrypt

from app.config import settings
from app.database import db
from app.utils.helpers import utcnow


async def ensure_demo_user() -> None:
    """Make sure the allowed account exists with the configured password and the admin role.

    Runs on every startup, so changing DEMO_PASSWORD in backend/.env takes effect after a restart.
    """
    email = settings.DEMO_EMAIL.lower()
    password_hash = bcrypt.hashpw(settings.DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one(
        {"email": email},
        {
            "$set": {"name": "Admin", "password_hash": password_hash, "role": "admin"},
            "$setOnInsert": {"created_at": utcnow()},
        },
        upsert=True,
    )
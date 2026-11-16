"""Async MongoDB connection (Motor) and index setup."""

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

# tz_aware=True makes MongoDB return timezone-aware (UTC) datetimes, so timestamps
# serialise with an explicit offset instead of being mistaken for local time.
client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000, tz_aware=True)
db = client[settings.MONGO_DB]


async def init_db() -> None:
    """Verify the connection and create the indexes the app relies on.

    Raises if MongoDB is unreachable; main.py catches this so the API still
    starts and /health can report the problem.
    """
    await client.admin.command("ping")
    await db.users.create_index("email", unique=True)
    await db.audit_logs.create_index([("timestamp", -1)])
    await db.scan_results.create_index([("scanned_at", -1)])
    await db.scan_results.create_index("image")
    await db.alerts.create_index([("detected_at", -1)])
    await db.alerts.create_index("acknowledged")


async def close_db() -> None:
    """Close the connection pool on shutdown."""
    client.close()

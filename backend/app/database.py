from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[settings.MONGO_DB]


async def init_db() -> None:
    await client.admin.command("ping")
    await db.users.create_index("email", unique=True)
    await db.audit_logs.create_index([("timestamp", -1)])


async def close_db() -> None:
    client.close()
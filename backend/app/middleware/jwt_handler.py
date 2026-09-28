from datetime import timedelta

import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.database import db
from app.utils.helpers import utcnow

bearer = HTTPBearer(auto_error=False)


def create_access_token(user_id: str, role: str) -> str:
    now = utcnow()
    payload = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if creds is None:
        raise unauthorized
    try:
        payload = decode_access_token(creds.credentials)
    except jwt.PyJWTError:
        raise unauthorized
    try:
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
    except Exception:
        raise unauthorized
    if not user:
        raise unauthorized
    return user
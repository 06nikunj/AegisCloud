"""Registration, login, current-user and (admin) role management."""

import bcrypt
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pymongo.errors import DuplicateKeyError

from app.config import settings
from app.database import db
from app.middleware.jwt_handler import create_access_token, get_current_user
from app.middleware.rbac import require_roles
from app.models.user import Role, RoleUpdate, TokenResponse, UserCreate, UserLogin, UserPublic
from app.utils.helpers import log_audit, utcnow

router = APIRouter()


def hash_password(password: str) -> str:
    """bcrypt-hash a password (the salt is embedded in the result)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Constant-time check of a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def to_public(user: dict) -> UserPublic:
    """Convert a MongoDB user document into the safe public shape."""
    return UserPublic(id=str(user["_id"]), name=user["name"], email=user["email"], role=user["role"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, request: Request):
    """Create an account. Disabled in single-account mode."""
    if settings.SINGLE_ACCOUNT_MODE:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sign-up is turned off.")

    is_first = await db.users.count_documents({}) == 0
    doc = {
        "name": body.name.strip(),
        "email": body.email.lower(),
        "password_hash": hash_password(body.password),
        "role": Role.admin.value if is_first else Role.viewer.value,
        "created_at": utcnow(),
    }
    try:
        result = await db.users.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    doc["_id"] = result.inserted_id
    await log_audit("auth.register", request, doc["email"], {"role": doc["role"]})
    token = create_access_token(str(doc["_id"]), doc["role"])
    return TokenResponse(access_token=token, user=to_public(doc))


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, request: Request):
    """Sign in. In single-account mode only the allowed email is accepted."""
    email = body.email.lower()
    if settings.SINGLE_ACCOUNT_MODE and email != settings.DEMO_EMAIL.lower():
        await log_audit("auth.login_failed", request, email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        await log_audit("auth.login_failed", request, email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    await log_audit("auth.login", request, email)
    token = create_access_token(str(user["_id"]), user["role"])
    return TokenResponse(access_token=token, user=to_public(user))


@router.get("/me", response_model=UserPublic)
async def me(user: dict = Depends(get_current_user)):
    """The currently logged-in user."""
    return to_public(user)


@router.get("/users", response_model=list[UserPublic])
async def list_users(admin: dict = Depends(require_roles("admin"))):
    """All users, oldest first (admin only)."""
    return [to_public(u) async for u in db.users.find().sort("created_at", 1)]


@router.put("/users/{user_id}/role", response_model=UserPublic)
async def set_user_role(user_id: str, body: RoleUpdate, request: Request,
                        admin: dict = Depends(require_roles("admin"))):
    """Change a user's role (admin only). Admins can't demote themselves, so the system always keeps one."""
    try:
        object_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That user ID isn't valid.")
    if object_id == admin["_id"] and body.role != Role.admin:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't remove your own admin role.")

    result = await db.users.update_one({"_id": object_id}, {"$set": {"role": body.role.value}})
    if result.matched_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")

    user = await db.users.find_one({"_id": object_id})
    await log_audit("auth.role_changed", request, admin["email"], {"target": user["email"], "role": body.role.value})
    return to_public(user)
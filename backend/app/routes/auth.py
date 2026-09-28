import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pymongo.errors import DuplicateKeyError

from app.database import db
from app.middleware.jwt_handler import create_access_token, get_current_user
from app.models.user import Role, TokenResponse, UserCreate, UserLogin, UserPublic
from app.utils.helpers import log_audit, utcnow

router = APIRouter()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def to_public(user: dict) -> UserPublic:
    return UserPublic(id=str(user["_id"]), name=user["name"], email=user["email"], role=user["role"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, request: Request):
    # First account becomes admin; everyone after that starts as viewer.
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
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    doc["_id"] = result.inserted_id
    await log_audit("auth.register", request, doc["email"], {"role": doc["role"]})
    token = create_access_token(str(doc["_id"]), doc["role"])
    return TokenResponse(access_token=token, user=to_public(doc))


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, request: Request):
    email = body.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        await log_audit("auth.login_failed", request, email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    await log_audit("auth.login", request, email)
    token = create_access_token(str(user["_id"]), user["role"])
    return TokenResponse(access_token=token, user=to_public(user))


@router.get("/me", response_model=UserPublic)
async def me(user: dict = Depends(get_current_user)):
    return to_public(user)
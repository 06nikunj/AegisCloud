"""Pydantic schemas for users and authentication."""

from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class Role(str, Enum):
    """Access levels. admin: everything. analyst: scan, acknowledge, AI, reports. viewer: read-only."""
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class UserCreate(BaseModel):
    """Body for POST /api/auth/register."""
    name: str = Field(min_length=2, max_length=60)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Body for POST /api/auth/login."""
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    """A user as returned by the API (never includes the password hash)."""
    id: str
    name: str
    email: EmailStr
    role: Role


class RoleUpdate(BaseModel):
    """Body for PUT /api/auth/users/{id}/role (admin only)."""
    role: Role


class TokenResponse(BaseModel):
    """Returned by login and register."""
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
from fastapi import Depends, HTTPException, status

from app.middleware.jwt_handler import get_current_user


def require_roles(*allowed: str):
    """Dependency factory: `Depends(require_roles("admin", "analyst"))`."""
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You don't have permission to do this")
        return user
    return checker
from fastapi import APIRouter, Depends

from app.database import db
from app.middleware.jwt_handler import get_current_user

router = APIRouter()


@router.get("/summary")
async def summary(user: dict = Depends(get_current_user)):
    """Week 1: real audit activity, zeroed security counts. Trivy/Falco fill these in Weeks 2-3."""
    recent = []
    async for entry in db.audit_logs.find().sort("timestamp", -1).limit(8):
        recent.append({
            "action": entry["action"],
            "user_email": entry.get("user_email"),
            "timestamp": entry["timestamp"].isoformat(),
        })
    return {
        "risk_score": 0,
        "scans_total": await db.scan_results.count_documents({}),
        "alerts_total": await db.alerts.count_documents({}),
        "severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        "recent_activity": recent,
    }
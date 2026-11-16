"""Dashboard summary: posture totals, risk score and recent activity."""

from fastapi import APIRouter, Depends

from app.database import db
from app.middleware.jwt_handler import get_current_user
from app.utils.helpers import compute_risk_score, iso, latest_severity_totals

router = APIRouter()


@router.get("/summary")
async def summary(user: dict = Depends(get_current_user)):
    """Everything the dashboard needs in one call.

    Severity totals use the latest scan of each image (re-scanning replaces, not adds),
    and the risk score is computed from those totals.
    """
    totals = await latest_severity_totals()

    recent = []
    async for entry in db.audit_logs.find().sort("timestamp", -1).limit(8):
        recent.append({
            "action": entry["action"],
            "user_email": entry.get("user_email"),
            "timestamp": iso(entry["timestamp"]),
        })

    return {
        "risk_score": compute_risk_score(totals),
        "scans_total": await db.scan_results.count_documents({}),
        "alerts_total": await db.alerts.count_documents({"acknowledged": False}),
        "severity": {
            "critical": totals["CRITICAL"],
            "high": totals["HIGH"],
            "medium": totals["MEDIUM"],
            "low": totals["LOW"],
        },
        "recent_activity": recent,
    }
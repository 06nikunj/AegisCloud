"""Runtime alerts: Falco webhook receiver, alert list and acknowledgement."""

import hmac

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Request, status

from app.config import settings
from app.database import db
from app.middleware.jwt_handler import get_current_user
from app.middleware.rbac import require_roles
from app.models.alert import FalcoEvent
from app.services import falco_service, sns_service
from app.utils.helpers import iso, log_audit
from app.utils.metrics import ALERTS_RECEIVED, NOTIFICATIONS_SENT

router = APIRouter()


def to_public(doc: dict) -> dict:
    """Shape an alert document for the API."""
    return {
        "id": str(doc["_id"]),
        "rule": doc.get("rule", "Unknown rule"),
        "priority": doc.get("priority", "low"),
        "container_name": doc.get("container_name", "unknown"),
        "command": doc.get("command", ""),
        "output": doc.get("output", ""),
        "acknowledged": doc.get("acknowledged", False),
        "simulated": doc.get("simulated", False),
        "detected_at": iso(doc["detected_at"]),
    }


def _check_webhook_secret(provided: str | None) -> None:
    """Reject webhook calls that don't carry the shared secret (skipped when none is configured)."""
    expected = settings.FALCO_WEBHOOK_SECRET
    if not expected:
        return
    if not provided or not hmac.compare_digest(provided.encode(), expected.encode()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid webhook secret.")


@router.post("/falco", status_code=status.HTTP_201_CREATED)
async def receive_falco_event(
    event: FalcoEvent,
    background: BackgroundTasks,
    x_falco_secret: str | None = Header(default=None),
    x_aegis_simulated: str | None = Header(default=None),
):
    """Webhook that Falco (or the demo simulator) posts detections to.

    Authenticated with the X-Falco-Secret header instead of a user login, because
    Falco is a service, not a person. Critical alerts trigger an SNS notification.
    """
    _check_webhook_secret(x_falco_secret)

    alert = falco_service.build_alert(event, simulated=(x_aegis_simulated or "").lower() == "true")
    result = await db.alerts.insert_one(alert)
    ALERTS_RECEIVED.labels(priority=alert["priority"]).inc()

    if falco_service.should_notify(alert["priority"]) and sns_service.is_configured():
        NOTIFICATIONS_SENT.labels(kind="alert").inc()
        background.add_task(sns_service.send_alert, *sns_service.format_alert_message(alert))

    return {"id": str(result.inserted_id), "priority": alert["priority"]}


@router.get("")
async def list_alerts(limit: int = Query(50, ge=1, le=200), user: dict = Depends(get_current_user)):
    """Most recent alerts first."""
    cursor = db.alerts.find().sort("detected_at", -1).limit(limit)
    return [to_public(doc) async for doc in cursor]


@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, request: Request,
                            user: dict = Depends(require_roles("admin", "analyst"))):
    """Mark an alert as reviewed."""
    try:
        object_id = ObjectId(alert_id)
    except InvalidId:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That alert ID isn't valid.")

    result = await db.alerts.update_one({"_id": object_id}, {"$set": {"acknowledged": True}})
    if result.matched_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found.")

    await log_audit("alerts.acknowledged", request, user["email"], {"alert_id": alert_id})
    return to_public(await db.alerts.find_one({"_id": object_id}))
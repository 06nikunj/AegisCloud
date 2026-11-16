"""Docker image scanning with Trivy."""

import asyncio

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status

from app.config import settings
from app.database import db
from app.middleware.jwt_handler import get_current_user
from app.middleware.rbac import require_roles
from app.models.scan_result import ScanRequest
from app.models.vulnerability import SEVERITY_RANK
from app.services import sns_service
from app.services.trivy_service import TrivyNotInstalledError, TrivyScanError, run_trivy_scan
from app.utils.helpers import compute_risk_score, count_by_severity, iso, log_audit, utcnow, validate_image_ref
from app.utils.metrics import NOTIFICATIONS_SENT, SCANS_TOTAL

router = APIRouter()

# Trivy is CPU and network heavy; cap how many scans run at once.
_scan_slots = asyncio.Semaphore(settings.MAX_CONCURRENT_SCANS)


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def scan_image(body: ScanRequest, request: Request, background: BackgroundTasks,
                     user: dict = Depends(require_roles("admin", "analyst"))):
    """Scan an image with Trivy, store the result, and return a summary.

    Trivy runs in a worker thread so a slow scan never freezes the rest of the API.
    If critical vulnerabilities are found, an SNS notification is sent in the background.
    """
    try:
        image = validate_image_ref(body.image)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    try:
        async with _scan_slots:
            vulnerabilities = await asyncio.to_thread(run_trivy_scan, image)
    except TrivyNotInstalledError as exc:
        SCANS_TOTAL.labels(result="failed").inc()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    except TrivyScanError as exc:
        SCANS_TOTAL.labels(result="failed").inc()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    counts = count_by_severity(vulnerabilities)
    risk_score = compute_risk_score(counts)
    doc = {
        "image": image,
        "user_email": user["email"],
        "scanned_at": utcnow(),
        "vulnerabilities": vulnerabilities,
        "severity_counts": counts,
        "risk_score": risk_score,
        "total": sum(counts.values()),
    }
    result = await db.scan_results.insert_one(doc)
    SCANS_TOTAL.labels(result="completed").inc()
    await log_audit("scan.completed", request, user["email"],
                    {"image": image, "total": doc["total"], "risk_score": risk_score})

    if counts["CRITICAL"] and "critical" in settings.sns_priorities and sns_service.is_configured():
        NOTIFICATIONS_SENT.labels(kind="scan").inc()
        background.add_task(sns_service.send_alert, *sns_service.format_scan_message(image, counts, risk_score))

    return {
        "id": str(result.inserted_id),
        "image": image,
        "scanned_at": iso(doc["scanned_at"]),
        "severity_counts": counts,
        "risk_score": risk_score,
        "total": doc["total"],
    }


@router.get("/results")
async def list_scan_results(limit: int = Query(50, ge=1, le=200), user: dict = Depends(get_current_user)):
    """Recent scans, newest first. Summary only: the CVE list is fetched per scan."""
    cursor = db.scan_results.find({}, {"vulnerabilities": 0}).sort("scanned_at", -1).limit(limit)
    return [{
        "id": str(doc["_id"]),
        "image": doc["image"],
        "scanned_by": doc.get("user_email", "unknown"),
        "scanned_at": iso(doc["scanned_at"]),
        "severity_counts": doc.get("severity_counts", {}),
        "risk_score": doc.get("risk_score", 0),
        "total": doc.get("total", 0),
    } async for doc in cursor]


@router.get("/results/{scan_id}/vulnerabilities")
async def get_scan_vulnerabilities(scan_id: str, user: dict = Depends(get_current_user)):
    """Full CVE list for one scan, worst severity first."""
    try:
        object_id = ObjectId(scan_id)
    except InvalidId:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That scan ID isn't valid.")

    doc = await db.scan_results.find_one({"_id": object_id})
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scan not found.")

    vulnerabilities = sorted(
        doc.get("vulnerabilities", []),
        key=lambda v: SEVERITY_RANK.get(v.get("Severity", "UNKNOWN"), len(SEVERITY_RANK)),
    )
    return {
        "id": str(doc["_id"]),
        "image": doc["image"],
        "scanned_at": iso(doc["scanned_at"]),
        "vulnerabilities": vulnerabilities,
    }
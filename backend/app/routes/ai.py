"""AI vulnerability analysis (Google Gemini)."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.config import settings
from app.middleware.jwt_handler import get_current_user
from app.middleware.rbac import require_roles
from app.services.ai_service import AINotConfiguredError, AIServiceError, analyze_vulnerability
from app.utils.helpers import log_audit

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Body for POST /api/ai/analyze."""
    cve_id: str = Field(min_length=3, max_length=40, examples=["CVE-2021-44228"])
    package: str = Field(default="", max_length=120)
    severity: str = Field(default="UNKNOWN", max_length=20)
    description: str = Field(default="", max_length=2000)


class AnalysisResponse(BaseModel):
    """Structured three-part explanation returned to the UI."""
    what_it_is: str
    attack_scenario: str
    remediation: list[str]
    model: str


@router.get("/status")
async def ai_status(user: dict = Depends(get_current_user)):
    """Whether the AI provider is configured. Used by the Metrics page."""
    return {
        "provider": "Google Gemini",
        "model": settings.GEMINI_MODEL,
        "configured": bool(settings.GEMINI_API_KEY),
    }


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(body: AnalyzeRequest, request: Request,
                  user: dict = Depends(require_roles("admin", "analyst"))):
    """Explain a vulnerability: what it is, how it is attacked, and how to fix it."""
    try:
        result = await analyze_vulnerability(
            body.cve_id.strip(), body.package.strip(), body.severity.strip().upper(), body.description.strip(),
        )
    except AINotConfiguredError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    except AIServiceError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))

    await log_audit("ai.analyzed", request, user["email"], {"cve_id": body.cve_id.strip()})
    return result
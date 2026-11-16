"""Downloadable scan reports (CSV and PDF)."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.middleware.rbac import require_roles
from app.services.report_service import generate_csv_report, generate_pdf_report

router = APIRouter()


@router.get("/csv")
async def download_csv(image: str | None = Query(default=None, max_length=200),
                       user: dict = Depends(require_roles("admin", "analyst"))):
    """Scan history as a CSV file, optionally filtered to one image."""
    return StreamingResponse(
        await generate_csv_report(image), media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="aegiscloud-scan-report.csv"'},
    )


@router.get("/pdf")
async def download_pdf(image: str | None = Query(default=None, max_length=200),
                       user: dict = Depends(require_roles("admin", "analyst"))):
    """Scan history as a formatted PDF, optionally filtered to one image."""
    return StreamingResponse(
        await generate_pdf_report(image), media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="aegiscloud-scan-report.pdf"'},
    )
"""Schemas for image scanning."""

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    """Body for POST /api/scan/image. The image reference is validated in the route."""
    image: str = Field(min_length=1, max_length=200, examples=["nginx:latest"])
"""Schemas for runtime alerts."""

from typing import Any

from pydantic import BaseModel, Field


class FalcoEvent(BaseModel):
    """The JSON body Falco's http_output sends for each detection.

    Falco adds extra fields over time; unknown ones are ignored.
    """
    rule: str = Field(min_length=1, max_length=200)
    priority: str = Field(default="Notice", max_length=30)
    output: str = Field(default="", max_length=4000)
    time: str | None = None
    hostname: str | None = None
    source: str | None = None
    tags: list[str] = Field(default_factory=list)
    output_fields: dict[str, Any] = Field(default_factory=dict)
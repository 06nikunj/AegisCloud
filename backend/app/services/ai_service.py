"""
AI threat-intelligence service: explains a CVE in plain English using Google Gemini.

Calls the Gemini REST API directly with httpx (already a project dependency), so no
extra SDK is needed. The model is asked for strict JSON, which is validated before
being returned to the route.
"""

import json
import logging
import re

import httpx

from app.config import settings

logger = logging.getLogger("aegiscloud.ai")

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

PROMPT = """You are a senior cloud security engineer explaining a vulnerability to a developer
who is not a security specialist. Avoid jargon; define any technical term you must use.

Vulnerability
- ID: {cve_id}
- Package: {package}
- Severity: {severity}
- Description: {description}

Respond with ONLY a JSON object (no markdown, no code fences) with exactly these keys:
what_it_is: a string of 2 to 3 sentences explaining the flaw in plain English.
attack_scenario: a string of 3 to 4 sentences describing how an attacker would realistically exploit it against a containerised application.
remediation: an array of 3 to 5 short strings, each one concrete step to fix or mitigate it.

If you are not certain about this specific CVE, say so in what_it_is rather than guessing details."""


class AINotConfiguredError(Exception):
    """Raised when no Gemini API key has been set."""


class AIServiceError(Exception):
    """Raised when the AI provider fails; the message is safe to show to the user."""


async def analyze_vulnerability(cve_id: str, package: str, severity: str, description: str) -> dict:
    """Return {what_it_is, attack_scenario, remediation, model} for the given vulnerability."""
    if not settings.GEMINI_API_KEY:
        raise AINotConfiguredError(
            "The AI engine isn't configured. Add GEMINI_API_KEY to backend/.env and restart the backend."
        )

    prompt = PROMPT.format(
        cve_id=cve_id,
        package=package or "not specified",
        severity=severity or "UNKNOWN",
        description=description or "not provided",
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"},
    }
    url = GEMINI_URL.format(model=settings.GEMINI_MODEL)

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(url, json=payload, headers={"x-goog-api-key": settings.GEMINI_API_KEY})
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        if code in (400, 401, 403):
            raise AIServiceError("Gemini rejected the request. Check that GEMINI_API_KEY in backend/.env is valid.")
        if code == 404:
            raise AIServiceError(
                f"Model '{settings.GEMINI_MODEL}' wasn't found. Set GEMINI_MODEL in backend/.env to a model your key can use."
            )
        if code == 429:
            raise AIServiceError("Gemini rate limit reached. Wait a minute and try again.")
        raise AIServiceError(f"Gemini returned an error ({code}). Try again shortly.")
    except httpx.TimeoutException:
        logger.warning("Gemini request timed out", exc_info=True)
        raise AIServiceError(
            "Gemini didn't respond in time. If this keeps happening, a firewall, VPN or slow network is blocking it."
        )
    except httpx.ConnectError as exc:
        logger.warning("Could not connect to Gemini", exc_info=True)
        if "certificate" in str(exc).lower() or "ssl" in str(exc).lower():
            raise AIServiceError(
                "A secure connection to Gemini couldn't be verified. Antivirus HTTPS scanning, a proxy or a "
                "college/office network is probably intercepting it."
            )
        raise AIServiceError(
            "Couldn't connect to generativelanguage.googleapis.com. Check your internet, VPN, proxy or firewall."
        )
    except httpx.HTTPError:
        logger.warning("Gemini request failed", exc_info=True)
        raise AIServiceError("Couldn't reach Gemini. The backend terminal shows the technical reason.")

    try:
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
        parsed = json.loads(text)
        remediation = parsed.get("remediation", [])
        if isinstance(remediation, str):
            remediation = [remediation]
        return {
            "what_it_is": str(parsed["what_it_is"]),
            "attack_scenario": str(parsed["attack_scenario"]),
            "remediation": [str(step) for step in remediation],
            "model": settings.GEMINI_MODEL,
        }
    except (KeyError, IndexError, ValueError, TypeError, AttributeError):
        raise AIServiceError("Gemini returned an unexpected response. Try again.")
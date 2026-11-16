"""
Wraps the Trivy CLI to scan a Docker image for known vulnerabilities (CVEs).

Trivy must be installed and on the system PATH. This module runs
`trivy image --format json <image>` and flattens the result into a simple list of
vulnerability dicts, so the rest of the backend never deals with Trivy's nested report.
"""

import json
import logging
import os
import re
import shutil
import subprocess

from app.config import settings

logger = logging.getLogger("aegiscloud.trivy")

# Where Trivy gets the image from. "remote" pulls straight from the registry, which is what a
# server scanning public images wants. Use "docker,remote" to prefer images already in local Docker.
IMAGE_SOURCE = os.getenv("TRIVY_IMAGE_SRC", "remote")


class TrivyNotInstalledError(Exception):
    """Raised when the `trivy` binary isn't found on PATH."""


class TrivyScanError(Exception):
    """Raised when Trivy ran but the scan failed (bad image name, network, timeout...)."""


def is_trivy_installed() -> bool:
    """True if the trivy command can be found."""
    return shutil.which("trivy") is not None


def explain_failure(image: str, stderr: str) -> str:
    """Turn Trivy's raw error output into a short, actionable message.

    Trivy's own errors are long and nested ("4 errors occurred ..."), and the real cause
    is usually at the end. Known causes get a plain-English explanation; anything else
    falls back to the last part of the output, with log timestamps and colour codes removed.
    """
    text = (stderr or "").lower()

    if "vulnerability db" in text or "db error" in text:
        return ("Trivy couldn't download its vulnerability database. Check your internet connection "
                "(it downloads from ghcr.io) and try again.")
    if "toomanyrequests" in text or "rate limit" in text or "too many requests" in text:
        return (f"Docker Hub's pull rate limit was reached while fetching '{image}'. Wait a while, run "
                "`docker login`, or scan the same image from AWS Public ECR "
                "(public.ecr.aws/docker/library/<name>:<tag>).")
    if "x509" in text or "certificate" in text:
        return ("A secure connection to the image registry couldn't be verified. Antivirus HTTPS scanning "
                "or a proxy on your network is probably intercepting it.")
    if any(hint in text for hint in ("no such host", "i/o timeout", "network is unreachable",
                                     "tls handshake timeout", "context deadline exceeded",
                                     "connection reset", "proxyconnect", "dial tcp")):
        return (f"Couldn't reach the image registry to download '{image}'. Check your internet, VPN, "
                "proxy or firewall (or try a phone hotspot).")
    if "manifest unknown" in text or "name unknown" in text or "manifest_unknown" in text \
            or "name_unknown" in text or "repository does not exist" in text:
        return f"'{image}' wasn't found in the registry. Check the image name and tag."
    if "unauthorized" in text or "denied" in text:
        return f"'{image}' is private or needs a login. Only public images can be scanned without credentials."

    cleaned = re.sub(r"\x1b\[[0-9;]*m", "", stderr or "")                        # colour codes
    cleaned = re.sub(r"\d{4}-\d{2}-\d{2}T[\d:.+\-]+\s*", "", cleaned)             # log timestamps
    cleaned = " ".join(cleaned.split())
    tail = cleaned[-350:] if cleaned else "no details were returned"
    return f"Trivy couldn't scan '{image}'. {tail}"


def run_trivy_scan(image: str) -> list[dict]:
    """Scan an image and return a flat list of vulnerabilities.

    Each item looks like:
        {"VulnerabilityID": "CVE-2023-1234", "PkgName": "openssl", "InstalledVersion": "1.1.1",
         "FixedVersion": "1.1.1n", "Severity": "HIGH", "Title": "...", "Description": "..."}

    This is a blocking call (it can take minutes), so async code must run it in a
    worker thread: `await asyncio.to_thread(run_trivy_scan, image)`.

    Raises TrivyNotInstalledError or TrivyScanError with a message that is safe to show the user.
    """
    if not is_trivy_installed():
        raise TrivyNotInstalledError(
            "Trivy isn't installed on this server. Install it and make sure the `trivy` "
            "command works from a terminal, then try again."
        )

    image = image.strip()
    if not image:
        raise TrivyScanError("No image name was provided.")

    timeout = settings.TRIVY_TIMEOUT_SECONDS
    command = [
        "trivy", "image",
        "--format", "json",
        "--quiet",
        "--scanners", "vuln",          # skip secret scanning: much faster, and we only report CVEs
        "--image-src", IMAGE_SOURCE,   # pull from the registry; don't probe local Docker/containerd/Podman
        "--skip-version-check",        # no extra network call just to look for a newer Trivy
        "--timeout", f"{timeout}s",
        image,
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout + 10)
    except subprocess.TimeoutExpired:
        raise TrivyScanError(f"Scanning '{image}' timed out. Try again or check your connection.")
    except FileNotFoundError:
        raise TrivyNotInstalledError("Trivy isn't installed or isn't on PATH.")

    if result.returncode != 0:
        logger.warning("Trivy failed for %s:\n%s", image, result.stderr)
        raise TrivyScanError(explain_failure(image, result.stderr))

    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise TrivyScanError("Trivy returned an unreadable report. Try again.")

    vulnerabilities = []
    for target in report.get("Results", []) or []:
        for vuln in target.get("Vulnerabilities", []) or []:
            vulnerabilities.append({
                "VulnerabilityID": vuln.get("VulnerabilityID", "UNKNOWN"),
                "PkgName": vuln.get("PkgName", "unknown"),
                "InstalledVersion": vuln.get("InstalledVersion", ""),
                "FixedVersion": vuln.get("FixedVersion", ""),
                "Severity": str(vuln.get("Severity", "UNKNOWN")).upper(),
                "Title": vuln.get("Title", ""),
                "Description": (vuln.get("Description") or "")[:500],  # keep documents small
            })
    return vulnerabilities
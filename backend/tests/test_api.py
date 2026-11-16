"""
API test-suite for AegisCloud.

Runs with no MongoDB, Trivy, AWS or Gemini: the database is an in-memory fake
(mongomock-motor) and the external services are replaced with stubs. Run with:

    cd backend
    pytest -v
"""

import asyncio

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import main
from app import database
from app.config import settings
from app.middleware import jwt_handler
from app.routes import alerts as alert_routes
from app.routes import auth as auth_routes
from app.routes import dashboard as dashboard_routes
from app.routes import scan as scan_routes
from app.services import falco_service, report_service, sns_service
from app.utils import helpers, metrics

PASSWORD = "Password123"

FAKE_VULNS = [
    {"VulnerabilityID": "CVE-2024-0001", "PkgName": "zlib", "InstalledVersion": "1.0", "FixedVersion": "1.1",
     "Severity": "LOW", "Title": "low issue", "Description": ""},
    {"VulnerabilityID": "CVE-2024-0002", "PkgName": "openssl", "InstalledVersion": "3.0", "FixedVersion": "3.1",
     "Severity": "CRITICAL", "Title": "critical issue", "Description": ""},
    {"VulnerabilityID": "CVE-2024-0003", "PkgName": "curl", "InstalledVersion": "8.0", "FixedVersion": "",
     "Severity": "HIGH", "Title": "high issue", "Description": ""},
]

FALCO_EVENT = {
    "rule": "Terminal shell in container",
    "priority": "Critical",
    "output": "A shell was spawned in container web-1",
    "time": "2026-10-25T10:20:30.123456789Z",
    "output_fields": {"container.name": "web-1", "proc.cmdline": "bash -i"},
}


# --------------------------------------------------------------------------- fixtures
@pytest.fixture()
def client(monkeypatch):
    """A TestClient wired to a fresh in-memory database for every test."""
    fake_client = AsyncMongoMockClient()
    fake_db = fake_client["aegiscloud_test"]
    for module in (database, helpers, jwt_handler, auth_routes, dashboard_routes,
                   scan_routes, alert_routes, report_service, metrics):
        monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(database, "client", fake_client)
    asyncio.run(fake_db.users.create_index("email", unique=True))

    monkeypatch.setattr(settings, "FALCO_WEBHOOK_SECRET", "")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "AWS_SNS_TOPIC_ARN", "")
    monkeypatch.setattr(settings, "SINGLE_ACCOUNT_MODE", False)
    return TestClient(main.app)


def register(client, email, name="Test User"):
    """Register a user; returns (token, user_id)."""
    res = client.post("/api/auth/register", json={"name": name, "email": email, "password": PASSWORD})
    assert res.status_code == 201, res.text
    body = res.json()
    return body["access_token"], body["user"]["id"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin(client):
    """The first registered account, which is always admin."""
    return register(client, "admin@example.com")[0]


@pytest.fixture()
def viewer(client, admin):
    return register(client, "viewer@example.com")[0]


@pytest.fixture()
def analyst(client, admin):
    token, user_id = register(client, "analyst@example.com")
    res = client.put(f"/api/auth/users/{user_id}/role", json={"role": "analyst"}, headers=auth(admin))
    assert res.status_code == 200
    return token


@pytest.fixture()
def fake_trivy(monkeypatch):
    monkeypatch.setattr(scan_routes, "run_trivy_scan", lambda image: [dict(v) for v in FAKE_VULNS])


@pytest.fixture()
def sns_calls(monkeypatch):
    """Capture SNS notifications instead of calling AWS."""
    calls = []

    async def fake_send(subject, message):
        calls.append((subject, message))
        return True

    monkeypatch.setattr(sns_service, "send_alert", fake_send)
    monkeypatch.setattr(sns_service, "is_configured", lambda: True)
    return calls


# --------------------------------------------------------------------------- auth
def test_first_user_is_admin_and_later_users_are_viewers(client):
    first = client.post("/api/auth/register", json={"name": "First", "email": "a@example.com", "password": PASSWORD})
    second = client.post("/api/auth/register", json={"name": "Second", "email": "b@example.com", "password": PASSWORD})
    assert first.json()["user"]["role"] == "admin"
    assert second.json()["user"]["role"] == "viewer"


def test_duplicate_email_is_rejected(client):
    register(client, "dupe@example.com")
    res = client.post("/api/auth/register", json={"name": "Again", "email": "DUPE@example.com", "password": PASSWORD})
    assert res.status_code == 409


def test_short_password_returns_a_readable_message(client):
    res = client.post("/api/auth/register", json={"name": "Shorty", "email": "s@example.com", "password": "short"})
    assert res.status_code == 422
    assert isinstance(res.json()["detail"], str)
    assert "password" in res.json()["detail"]


def test_login_success_and_failure(client):
    register(client, "login@example.com")
    ok = client.post("/api/auth/login", json={"email": "login@example.com", "password": PASSWORD})
    bad = client.post("/api/auth/login", json={"email": "login@example.com", "password": "wrong-password"})
    assert ok.status_code == 200 and ok.json()["access_token"]
    assert bad.status_code == 401


def test_protected_routes_require_a_token(client):
    for path in ("/api/auth/me", "/api/dashboard/summary", "/api/scan/results", "/api/alerts", "/api/ai/status"):
        assert client.get(path).status_code == 401, path


def test_me_returns_the_logged_in_user(client, admin):
    res = client.get("/api/auth/me", headers=auth(admin))
    assert res.status_code == 200
    assert res.json()["email"] == "admin@example.com"


# --------------------------------------------------------------------------- role management
def test_admin_can_change_roles_and_viewer_cannot_list_users(client, admin, viewer):
    users = client.get("/api/auth/users", headers=auth(admin))
    assert users.status_code == 200 and len(users.json()) == 2
    assert client.get("/api/auth/users", headers=auth(viewer)).status_code == 403


def test_admin_cannot_demote_themselves(client, admin):
    me = client.get("/api/auth/me", headers=auth(admin)).json()
    res = client.put(f"/api/auth/users/{me['id']}/role", json={"role": "viewer"}, headers=auth(admin))
    assert res.status_code == 400


def test_role_change_for_unknown_or_invalid_user(client, admin):
    assert client.put("/api/auth/users/not-an-id/role", json={"role": "analyst"}, headers=auth(admin)).status_code == 400
    missing = "507f1f77bcf86cd799439011"
    assert client.put(f"/api/auth/users/{missing}/role", json={"role": "analyst"}, headers=auth(admin)).status_code == 404


# --------------------------------------------------------------------------- scanning
def test_viewer_cannot_scan_but_analyst_can(client, viewer, analyst, fake_trivy):
    assert client.post("/api/scan/image", json={"image": "nginx:latest"}, headers=auth(viewer)).status_code == 403
    res = client.post("/api/scan/image", json={"image": "nginx:latest"}, headers=auth(analyst))
    assert res.status_code == 201
    body = res.json()
    assert body["severity_counts"] == {"CRITICAL": 1, "HIGH": 1, "MEDIUM": 0, "LOW": 1}
    assert body["total"] == 3 and 0 < body["risk_score"] < 100


@pytest.mark.parametrize("bad", ["--config=/etc/passwd", "-h", "nginx latest", "a;rm -rf /", "   "])
def test_malicious_or_invalid_image_names_are_rejected(client, admin, fake_trivy, bad):
    res = client.post("/api/scan/image", json={"image": bad}, headers=auth(admin))
    assert res.status_code in (400, 422)


def test_scan_results_and_vulnerabilities_are_sorted_worst_first(client, admin, fake_trivy):
    scan_id = client.post("/api/scan/image", json={"image": "nginx:latest"}, headers=auth(admin)).json()["id"]

    listing = client.get("/api/scan/results", headers=auth(admin)).json()
    assert len(listing) == 1 and "vulnerabilities" not in listing[0]

    detail = client.get(f"/api/scan/results/{scan_id}/vulnerabilities", headers=auth(admin)).json()
    assert [v["Severity"] for v in detail["vulnerabilities"]] == ["CRITICAL", "HIGH", "LOW"]


def test_scan_id_validation(client, admin):
    assert client.get("/api/scan/results/not-an-id/vulnerabilities", headers=auth(admin)).status_code == 400
    assert client.get("/api/scan/results/507f1f77bcf86cd799439011/vulnerabilities", headers=auth(admin)).status_code == 404


def test_trivy_not_installed_gives_a_503(client, admin, monkeypatch):
    from app.services.trivy_service import TrivyNotInstalledError

    def boom(image):
        raise TrivyNotInstalledError("Trivy isn't installed")

    monkeypatch.setattr(scan_routes, "run_trivy_scan", boom)
    res = client.post("/api/scan/image", json={"image": "nginx:latest"}, headers=auth(admin))
    assert res.status_code == 503


def test_critical_scan_triggers_an_sns_notification(client, admin, fake_trivy, sns_calls):
    client.post("/api/scan/image", json={"image": "nginx:latest"}, headers=auth(admin))
    assert len(sns_calls) == 1
    assert "critical" in sns_calls[0][0].lower()


# --------------------------------------------------------------------------- dashboard
def test_dashboard_is_empty_before_any_data(client, admin):
    data = client.get("/api/dashboard/summary", headers=auth(admin)).json()
    assert data["risk_score"] == 0 and data["scans_total"] == 0 and data["alerts_total"] == 0


def test_dashboard_counts_only_the_latest_scan_of_each_image(client, admin, fake_trivy):
    for _ in range(3):
        client.post("/api/scan/image", json={"image": "nginx:latest"}, headers=auth(admin))
    data = client.get("/api/dashboard/summary", headers=auth(admin)).json()
    assert data["scans_total"] == 3                      # history keeps all three scans...
    assert data["severity"] == {"critical": 1, "high": 1, "medium": 0, "low": 1}  # ...totals count one


# --------------------------------------------------------------------------- Falco webhook + alerts
def test_falco_webhook_stores_and_maps_the_alert(client, admin):
    res = client.post("/api/alerts/falco", json=FALCO_EVENT, headers={"X-Aegis-Simulated": "true"})
    assert res.status_code == 201 and res.json()["priority"] == "critical"

    alerts = client.get("/api/alerts", headers=auth(admin)).json()
    assert len(alerts) == 1
    assert alerts[0]["container_name"] == "web-1"
    assert alerts[0]["command"] == "bash -i"
    assert alerts[0]["simulated"] is True and alerts[0]["acknowledged"] is False
    assert alerts[0]["detected_at"].startswith("2026-10-25T10:20:30")


def test_falco_webhook_secret_is_enforced_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "FALCO_WEBHOOK_SECRET", "s3cret")
    assert client.post("/api/alerts/falco", json=FALCO_EVENT).status_code == 401
    assert client.post("/api/alerts/falco", json=FALCO_EVENT, headers={"X-Falco-Secret": "wrong"}).status_code == 401
    assert client.post("/api/alerts/falco", json=FALCO_EVENT, headers={"X-Falco-Secret": "s3cret"}).status_code == 201


def test_only_critical_alerts_trigger_sns(client, sns_calls):
    client.post("/api/alerts/falco", json={**FALCO_EVENT, "priority": "Warning"})
    assert sns_calls == []
    client.post("/api/alerts/falco", json={**FALCO_EVENT, "priority": "Critical"})
    assert len(sns_calls) == 1


def test_acknowledge_flow_and_permissions(client, admin, viewer):
    client.post("/api/alerts/falco", json=FALCO_EVENT)
    alert_id = client.get("/api/alerts", headers=auth(admin)).json()[0]["id"]

    assert client.put(f"/api/alerts/{alert_id}/acknowledge", headers=auth(viewer)).status_code == 403
    done = client.put(f"/api/alerts/{alert_id}/acknowledge", headers=auth(admin))
    assert done.status_code == 200 and done.json()["acknowledged"] is True
    assert client.get("/api/dashboard/summary", headers=auth(admin)).json()["alerts_total"] == 0

    assert client.put("/api/alerts/not-an-id/acknowledge", headers=auth(admin)).status_code == 400
    assert client.put("/api/alerts/507f1f77bcf86cd799439011/acknowledge", headers=auth(admin)).status_code == 404


def test_falco_event_without_a_rule_is_rejected(client):
    assert client.post("/api/alerts/falco", json={"priority": "Critical"}).status_code == 422


# --------------------------------------------------------------------------- AI
def test_ai_reports_not_configured(client, admin):
    assert client.get("/api/ai/status", headers=auth(admin)).json()["configured"] is False
    res = client.post("/api/ai/analyze", json={"cve_id": "CVE-2021-44228"}, headers=auth(admin))
    assert res.status_code == 503 and "GEMINI_API_KEY" in res.json()["detail"]


def test_ai_analyze_returns_structured_output(client, admin, monkeypatch):
    from app.routes import ai as ai_routes

    async def fake(cve_id, package, severity, description):
        return {"what_it_is": "A flaw.", "attack_scenario": "An attack.", "remediation": ["Patch it."], "model": "test"}

    monkeypatch.setattr(ai_routes, "analyze_vulnerability", fake)
    res = client.post("/api/ai/analyze", json={"cve_id": "CVE-2021-44228"}, headers=auth(admin))
    assert res.status_code == 200
    assert res.json()["remediation"] == ["Patch it."]


def test_viewer_cannot_use_ai_analysis(client, viewer):
    assert client.post("/api/ai/analyze", json={"cve_id": "CVE-2021-44228"}, headers=auth(viewer)).status_code == 403


# --------------------------------------------------------------------------- reports
def test_csv_and_pdf_reports(client, admin, fake_trivy):
    client.post("/api/scan/image", json={"image": "nginx:latest"}, headers=auth(admin))

    csv_res = client.get("/api/reports/csv", headers=auth(admin))
    assert csv_res.status_code == 200 and "nginx:latest" in csv_res.text
    assert "attachment" in csv_res.headers["content-disposition"]

    pdf_res = client.get("/api/reports/pdf", headers=auth(admin))
    assert pdf_res.status_code == 200 and pdf_res.content.startswith(b"%PDF")


def test_reports_work_with_no_scans(client, admin):
    assert "No scans recorded yet" in client.get("/api/reports/csv", headers=auth(admin)).text
    assert client.get("/api/reports/pdf", headers=auth(admin)).content.startswith(b"%PDF")


def test_reports_require_analyst_or_admin(client, viewer):
    assert client.get("/api/reports/csv", headers=auth(viewer)).status_code == 403


# --------------------------------------------------------------------------- system
def test_health_and_metrics(client, admin):
    health = client.get("/health").json()
    assert health["status"] == "ok" and health["database"] == "up"

    client.get("/api/dashboard/summary", headers=auth(admin))
    text = client.get("/metrics").text
    assert "aegis_http_requests_total" in text and "aegis_open_alerts" in text


# --------------------------------------------------------------------------- pure functions
def test_risk_score_properties():
    zero = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    one_crit = {**zero, "CRITICAL": 1}
    many = {"CRITICAL": 50, "HIGH": 200, "MEDIUM": 300, "LOW": 400}
    assert helpers.compute_risk_score(zero) == 0
    assert 0 < helpers.compute_risk_score(one_crit) < helpers.compute_risk_score({**zero, "CRITICAL": 5})
    assert helpers.compute_risk_score(many) <= 100


def test_count_by_severity_ignores_unknown_values():
    counts = helpers.count_by_severity([{"Severity": "high"}, {"Severity": "WEIRD"}, {}])
    assert counts == {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 0, "LOW": 0}


@pytest.mark.parametrize("good", ["nginx", "nginx:latest", "ubuntu:20.04", "ghcr.io/org/app:1.2", "app@sha256:abc123"])
def test_valid_image_refs(good):
    assert helpers.validate_image_ref(good) == good


@pytest.mark.parametrize("bad", ["", "  ", "--flag", "-x", "a b", "a;b", "a$(id)", "x" * 300])
def test_invalid_image_refs(bad):
    with pytest.raises(ValueError):
        helpers.validate_image_ref(bad)


def test_falco_priority_mapping_and_time_parsing():
    assert [falco_service.map_priority(p) for p in ("Emergency", "Critical", "Error", "Warning", "Notice", "nonsense")] == [
        "critical", "critical", "high", "medium", "low", "low"]
    parsed = falco_service.parse_event_time("2026-10-25T10:20:30.123456789Z")
    assert (parsed.year, parsed.hour, parsed.microsecond) == (2026, 10, 123456)
    assert parsed.tzinfo is not None
    assert falco_service.parse_event_time("garbage").tzinfo is not None   # falls back to "now"
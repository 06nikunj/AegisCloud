from fastapi.testclient import TestClient

from app.middleware.jwt_handler import create_access_token, decode_access_token
from app.routes.auth import hash_password, verify_password
from main import app


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse battery")
    assert hashed != "correct horse battery"
    assert verify_password("correct horse battery", hashed)
    assert not verify_password("wrong password", hashed)


def test_jwt_roundtrip():
    token = create_access_token("abc123", "admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "abc123"
    assert payload["role"] == "admin"


def test_protected_routes_require_token():
    client = TestClient(app)
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/dashboard/summary").status_code == 401
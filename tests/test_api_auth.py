"""Optional demo API rejects unauthenticated use."""
import os

from fastapi.testclient import TestClient
from agents.api import app

client = TestClient(app)


def test_health_is_public():
    response = client.get("/health")
    assert response.status_code == 200


def test_no_configured_secret_disables_api(monkeypatch):
    monkeypatch.delenv("AUDIT_API_KEY", raising=False)
    assert client.get("/metrics").status_code == 503
    assert client.post("/api/chat", json={"query": "hello"}).status_code == 503


def test_api_rejects_wrong_key_and_accepts_valid_key(monkeypatch):
    monkeypatch.setenv("AUDIT_API_KEY", "test-key-local-only")
    assert client.get("/metrics").status_code == 401
    assert client.get("/metrics", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/metrics", headers={"X-API-Key": "test-key-local-only"}).status_code == 200

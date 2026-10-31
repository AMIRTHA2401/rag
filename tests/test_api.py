from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_invalid_upload_type():
    response = TestClient(app).post("/api/documents/upload", files={"file": ("bad.exe", b"no", "application/octet-stream")})
    assert response.status_code == 415


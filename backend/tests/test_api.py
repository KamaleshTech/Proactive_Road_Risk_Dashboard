from fastapi.testclient import TestClient

from backend.main import app
from backend.storage import reset_demo_dataset


def test_health_and_dashboard():
    reset_demo_dataset()
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        dashboard = client.get("/api/dashboard")
        assert dashboard.status_code == 200
        body = dashboard.json()
        assert body["summary"]["records"] >= 12
        assert len(body["risk_bands"]) == 4
        assert body["map_points"]


def test_record_filters_and_csv_export():
    reset_demo_dataset()
    with TestClient(app) as client:
        options = client.get("/api/options").json()
        state = options["states"][0]
        response = client.get("/api/records", params={"state": state, "limit": 100})
        assert response.status_code == 200
        assert response.json()["total"] > 0
        assert all(row["state"] == state for row in response.json()["items"])
        export = client.get("/api/export.csv", params={"state": state})
        assert export.status_code == 200
        assert "text/csv" in export.headers["content-type"]


def test_upload_rejects_non_csv():
    with TestClient(app) as client:
        response = client.post("/api/upload", files={"file": ("bad.txt", "hello", "text/plain")})
        assert response.status_code == 400

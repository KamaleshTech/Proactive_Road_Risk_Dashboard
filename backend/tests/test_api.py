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



def test_valid_csv_upload_replaces_dataset_and_reports_bad_coordinates():
    reset_demo_dataset()
    csv_text = (
        "Start_Time,Start_Lat,Start_Lng,State,City,Severity,Weather_Condition,Visibility(mi),Sunrise_Sunset\n"
        "2023-01-01 12:00:00,39.1000,-84.5000,OH,Columbus,2,Clear,10,Day\n"
        "2023-01-01 13:00:00,,-84.6000,OH,Cincinnati,3,Rain,3,Night\n"
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/upload",
                files={"file": ("sample.csv", csv_text, "text/csv")},
            )
            assert response.status_code == 200, response.text
            metadata = response.json()["metadata"]
            assert metadata["name"] == "sample.csv"
            assert metadata["is_demo"] is False
            assert metadata["row_count"] == 1
            assert metadata["dropped_rows"] == 1

            dashboard = client.get("/api/dashboard").json()
            assert dashboard["summary"]["records"] == 1
            records = client.get("/api/records").json()["items"]
            assert len(records) == 1
            assert records[0]["city"] == "Columbus"

            exported = client.get("/api/export.csv")
            assert exported.status_code == 200
            assert "Columbus" in exported.text
    finally:
        reset_demo_dataset()

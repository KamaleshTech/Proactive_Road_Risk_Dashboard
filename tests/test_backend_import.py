from fastapi.testclient import TestClient
import pandas as pd
import pytest

from backend.analytics import demo_records, normalize_dataframe, score_record
from backend.main import app
from backend.storage import reset_demo_dataset


def test_demo_records_scores_and_bands_are_consistent():
    records = demo_records()
    assert len(records) >= 12
    assert all(0 <= row["risk_score"] <= 100 for row in records)
    assert all(row["risk_band"] in {"Low", "Guarded", "Elevated", "High"} for row in records)
    assert all(row["explanation"] for row in records)


def test_bad_weather_visibility_increases_heuristic_score():
    score, band, explanation = score_record({"visibility_mi": 1.0, "weather_condition": "Heavy Rain", "sunrise_sunset": "Night", "junction": True})
    assert score >= 60
    assert band in {"Elevated", "High"}
    assert "Low visibility" in explanation and "Severe weather" in explanation


def test_normalizes_source_dataset_fields_and_drops_bad_coordinates():
    raw = pd.DataFrame({"Start_Time": ["2023-01-01 12:30", "2023-01-01 13:00"], "Start_Lat": [39.0, None], "Start_Lng": [-84.0, -83.0], "State": ["OH", "OH"], "Severity": [2, 3], "Weather_Condition": ["Clear", "Rain"]})
    records, dropped = normalize_dataframe(raw)
    assert len(records) == 1 and dropped == 1
    assert records[0]["state"] == "OH" and records[0]["severity"] == 2


def test_missing_coordinates_raise_a_clear_error():
    with pytest.raises(ValueError, match="Required coordinate"):
        normalize_dataframe(pd.DataFrame({"State": ["OH"]}))


def test_api_health_dashboard_and_filter_work():
    reset_demo_dataset()
    with TestClient(app) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        dashboard = client.get("/api/dashboard").json()
        assert dashboard["summary"]["records"] >= 12
        assert len(dashboard["risk_bands"]) == 4
        state = client.get("/api/options").json()["states"][0]
        results = client.get("/api/records", params={"state": state, "limit": 100})
        assert results.status_code == 200 and results.json()["total"] > 0
        assert all(item["state"] == state for item in results.json()["items"])


def test_export_csv_and_invalid_upload():
    reset_demo_dataset()
    with TestClient(app) as client:
        csv = client.get("/api/export.csv")
        assert csv.status_code == 200 and "text/csv" in csv.headers["content-type"]
        bad = client.post("/api/upload", files={"file": ("bad.txt", "hello", "text/plain")})
        assert bad.status_code == 400

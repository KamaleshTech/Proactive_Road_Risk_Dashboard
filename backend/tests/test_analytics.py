import pandas as pd
import pytest

from backend.analytics import demo_records, normalize_dataframe, score_record


def test_demo_records_have_explainable_scores():
    rows = demo_records()
    assert len(rows) >= 12
    assert all(0 <= row["risk_score"] <= 100 for row in rows)
    assert all(row["risk_band"] in {"Low", "Guarded", "Elevated", "High"} for row in rows)
    assert all(row["explanation"] for row in rows)


def test_severe_weather_and_low_visibility_raise_indicator():
    score, band, explanation = score_record({
        "visibility_mi": 1.0,
        "weather_condition": "Heavy Rain",
        "sunrise_sunset": "Night",
        "junction": True,
    })
    assert score >= 60
    assert band in {"Elevated", "High"}
    assert "Low visibility" in explanation
    assert "Severe weather" in explanation


def test_normalizer_accepts_us_accidents_column_names():
    raw = pd.DataFrame({
        "Start_Time": ["2023-01-01 12:30:00", "2023-01-01 13:00:00"],
        "Start_Lat": [39.0, None],
        "Start_Lng": [-84.0, -83.0],
        "State": ["OH", "OH"],
        "Severity": [2, 3],
        "Weather_Condition": ["Clear", "Rain"],
    })
    rows, dropped = normalize_dataframe(raw)
    assert len(rows) == 1
    assert dropped == 1
    assert rows[0]["state"] == "OH"
    assert rows[0]["severity"] == 2


def test_normalizer_requires_coordinates():
    with pytest.raises(ValueError, match="Required coordinate"):
        normalize_dataframe(pd.DataFrame({"State": ["OH"]}))


def test_numeric_outliers_become_missing_not_crash():
    raw = pd.DataFrame({
        "Start_Lat": [39.0],
        "Start_Lng": [-84.0],
        "Temperature(F)": [999],
        "Humidity(%)": [500],
        "Visibility(mi)": [-2],
    })
    rows, _ = normalize_dataframe(raw)
    assert rows[0]["temperature_f"] is None
    assert rows[0]["humidity"] is None
    assert rows[0]["visibility_mi"] is None

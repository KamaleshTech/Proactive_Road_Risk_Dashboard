import pandas as pd
import pytest

from road_risk.analytics import add_historical_indicator, demo_data, normalize_dataframe


def test_demo_data_normalizes_and_scores():
    data, report = normalize_dataframe(demo_data())
    scored = add_historical_indicator(data)
    assert len(scored) == len(data)
    assert report.rows_in == report.rows_out
    assert scored["Historical_Risk_Indicator"].between(0, 100).all()
    assert set(scored["Indicator_Band"].dropna()).issubset({"Low", "Guarded", "Elevated", "High"})
    assert scored["Indicator_Explanation"].notna().all()


def test_invalid_coordinates_are_removed():
    raw = pd.DataFrame({
        "Start_Lat": [39.0, None, 100.0],
        "Start_Lng": [-80.0, -90.0, 200.0],
        "State": ["OH", "OH", "OH"],
    })
    data, report = normalize_dataframe(raw)
    assert len(data) == 1
    assert report.dropped_bad_coordinates == 2


def test_required_coordinates_are_enforced():
    with pytest.raises(ValueError, match="Start_Lat"):
        normalize_dataframe(pd.DataFrame({"Start_Lng": [-80], "State": ["OH"]}))


def test_empty_dataset_fails():
    with pytest.raises(ValueError, match="no rows"):
        normalize_dataframe(pd.DataFrame(columns=["Start_Lat", "Start_Lng"]))


def test_duplicate_columns_fail():
    raw = pd.DataFrame([[1, 2, 3]], columns=["Start_Lat", "Start_Lng", "Start_Lat"])
    with pytest.raises(ValueError, match="Duplicate column"):
        normalize_dataframe(raw)


def test_indicator_has_explainable_weather_visibility_night_reasons():
    raw = pd.DataFrame({
        "Start_Lat": [39.1], "Start_Lng": [-84.5], "Visibility(mi)": [1.0],
        "Weather_Condition": ["Heavy Rain"], "Sunrise_Sunset": ["Night"],
    })
    normalized, _ = normalize_dataframe(raw)
    scored = add_historical_indicator(normalized)
    assert scored.loc[0, "Historical_Risk_Indicator"] >= 50
    explanation = scored.loc[0, "Indicator_Explanation"]
    assert "Low visibility" in explanation
    assert "Severe weather" in explanation
    assert "Night-time" in explanation


def test_indicator_caps_at_100():
    raw = pd.DataFrame({
        "Start_Lat": [39.1], "Start_Lng": [-84.5], "Visibility(mi)": [0.1],
        "Weather_Condition": ["Thunderstorm, heavy rain, snow"], "Precipitation(in)": [2.0],
        "Wind_Speed(mph)": [70], "Humidity(%)": [99], "Sunrise_Sunset": ["Night"],
        "Junction": [True], "Traffic_Signal": [True], "Crossing": [True],
        "Railway": [True], "Stop": [True],
    })
    normalized, _ = normalize_dataframe(raw)
    scored = add_historical_indicator(normalized)
    assert scored.loc[0, "Historical_Risk_Indicator"] == 100

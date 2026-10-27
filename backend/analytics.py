"""CSV normalization and transparent historical indicator calculations."""
from __future__ import annotations

from datetime import datetime
import math
from typing import Any

import pandas as pd

MAX_IMPORT_ROWS = 100_000
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "start_time": ("Start_Time", "start_time", "timestamp", "datetime", "date"),
    "start_lat": ("Start_Lat", "start_lat", "latitude", "lat"),
    "start_lng": ("Start_Lng", "start_lng", "longitude", "lng", "lon", "long"),
    "state": ("State", "state", "region"),
    "city": ("City", "city", "town"),
    "severity": ("Severity", "severity"),
    "weather_condition": ("Weather_Condition", "weather_condition", "weather"),
    "temperature_f": ("Temperature(F)", "temperature_f", "temperature", "temp_f"),
    "humidity": ("Humidity(%)", "humidity", "humidity_pct"),
    "visibility_mi": ("Visibility(mi)", "visibility_mi", "visibility"),
    "wind_speed_mph": ("Wind_Speed(mph)", "wind_speed_mph", "wind_speed"),
    "precipitation_in": ("Precipitation(in)", "precipitation_in", "precipitation"),
    "junction": ("Junction", "junction"),
    "traffic_signal": ("Traffic_Signal", "traffic_signal"),
    "crossing": ("Crossing", "crossing"),
    "sunrise_sunset": ("Sunrise_Sunset", "sunrise_sunset", "day_night"),
}
NUMERIC_FIELDS = ("temperature_f", "humidity", "visibility_mi", "wind_speed_mph", "precipitation_in")
ROAD_FLAGS = ("junction", "traffic_signal", "crossing")


def _pick(row: pd.Series, candidates: tuple[str, ...]) -> Any:
    lower_to_actual = {str(name).strip().lower(): name for name in row.index}
    for candidate in candidates:
        actual = lower_to_actual.get(candidate.lower())
        if actual is not None:
            return row[actual]
    return None


def _text(value: Any, fallback: str = "Unknown") -> str:
    if value is None or pd.isna(value):
        return fallback
    text = str(value).strip()
    return text if text and text.lower() not in {"nan", "none", "null"} else fallback


def _number(value: Any, *, lower: float | None = None, upper: float | None = None) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        number = float(value)
        if not math.isfinite(number):
            return None
        if lower is not None and number < lower:
            return None
        if upper is not None and number > upper:
            return None
        return number
    except (TypeError, ValueError):
        return None


def _flag(value: Any) -> bool:
    if value is None or pd.isna(value):
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "y", "t"}


def score_record(record: dict[str, Any]) -> tuple[int, str, str]:
    """A transparent heuristic for sorting historical records; not a future-crash prediction."""
    score = 0
    reasons: list[str] = []

    visibility = record.get("visibility_mi")
    if visibility is not None and 0 <= visibility <= 3:
        score += 25
        reasons.append("Low visibility (≤3 mi)")
    elif visibility is not None and 3 < visibility <= 5:
        score += 12
        reasons.append("Reduced visibility (3–5 mi)")

    weather = str(record.get("weather_condition") or "").lower()
    severe_weather = any(term in weather for term in ("heavy rain", "thunder", "snow", "sleet", "ice", "freezing", "fog"))
    if severe_weather:
        score += 25
        reasons.append("Severe weather label")
    elif any(term in weather for term in ("rain", "drizzle", "overcast")):
        score += 10
        reasons.append("Wet or overcast weather label")

    precip = record.get("precipitation_in")
    if precip is not None and 0.25 <= precip < 10:
        score += 15
        reasons.append("Elevated precipitation")

    wind = record.get("wind_speed_mph")
    if wind is not None and 25 <= wind <= 150:
        score += 10
        reasons.append("High wind speed")

    humidity = record.get("humidity")
    if humidity is not None and 90 <= humidity <= 100:
        score += 8
        reasons.append("Very high humidity")

    if str(record.get("sunrise_sunset") or "").lower() == "night":
        score += 8
        reasons.append("Night-time record")

    for flag in ROAD_FLAGS:
        if record.get(flag):
            score += 5
            reasons.append(f"Road-context flag: {flag.replace('_', ' ')}")

    score = min(100, score)
    band = "High" if score >= 75 else "Elevated" if score >= 50 else "Guarded" if score >= 25 else "Low"
    explanation = "; ".join(reasons) if reasons else "No configured indicator signals detected"
    return score, band, explanation


def normalize_dataframe(raw: pd.DataFrame) -> tuple[list[dict[str, Any]], int]:
    """Normalize accepted CSV columns; discard only rows with invalid coordinates."""
    if raw.empty:
        raise ValueError("The CSV has no data rows.")
    raw.columns = [str(col).strip() for col in raw.columns]
    if raw.columns.duplicated().any():
        duplicate_names = raw.columns[raw.columns.duplicated()].tolist()
        raise ValueError(f"Duplicate column names: {duplicate_names}")

    # Require coordinates; all other fields are optional.
    lookup = {str(col).strip().lower(): col for col in raw.columns}
    coord_candidates = {
        "start_lat": FIELD_ALIASES["start_lat"],
        "start_lng": FIELD_ALIASES["start_lng"],
    }
    for key, candidates in coord_candidates.items():
        if not any(candidate.lower() in lookup for candidate in candidates):
            raise ValueError(f"Required coordinate column missing: {key} (Start_Lat / Start_Lng)")

    rows: list[dict[str, Any]] = []
    dropped = 0
    # Reset index so row keys are deterministic and valid even with a filtered input frame.
    for _, row in raw.iterrows():
        lat = _number(_pick(row, FIELD_ALIASES["start_lat"]), lower=-90, upper=90)
        lng = _number(_pick(row, FIELD_ALIASES["start_lng"]), lower=-180, upper=180)
        if lat is None or lng is None:
            dropped += 1
            continue

        time_value = _pick(row, FIELD_ALIASES["start_time"])
        start_time: str | None = None
        if time_value is not None and not pd.isna(time_value):
            parsed = pd.to_datetime(time_value, errors="coerce", format="mixed")
            if not pd.isna(parsed):
                start_time = parsed.isoformat()

        severity_num = _number(_pick(row, FIELD_ALIASES["severity"]), lower=1, upper=4)
        record: dict[str, Any] = {
            "start_time": start_time,
            "start_lat": lat,
            "start_lng": lng,
            "state": _text(_pick(row, FIELD_ALIASES["state"])),
            "city": _text(_pick(row, FIELD_ALIASES["city"])),
            "severity": int(severity_num) if severity_num is not None and severity_num.is_integer() else None,
            "weather_condition": _text(_pick(row, FIELD_ALIASES["weather_condition"]), fallback="Unknown"),
            "temperature_f": _number(_pick(row, FIELD_ALIASES["temperature_f"]), lower=-100, upper=160),
            "humidity": _number(_pick(row, FIELD_ALIASES["humidity"]), lower=0, upper=100),
            "visibility_mi": _number(_pick(row, FIELD_ALIASES["visibility_mi"]), lower=0, upper=200),
            "wind_speed_mph": _number(_pick(row, FIELD_ALIASES["wind_speed_mph"]), lower=0, upper=250),
            "precipitation_in": _number(_pick(row, FIELD_ALIASES["precipitation_in"]), lower=0, upper=100),
            "junction": _flag(_pick(row, FIELD_ALIASES["junction"])),
            "traffic_signal": _flag(_pick(row, FIELD_ALIASES["traffic_signal"])),
            "crossing": _flag(_pick(row, FIELD_ALIASES["crossing"])),
            "sunrise_sunset": _text(_pick(row, FIELD_ALIASES["sunrise_sunset"]), fallback="Unknown"),
        }
        score, band, explanation = score_record(record)
        record.update({"risk_score": score, "risk_band": band, "explanation": explanation})
        rows.append(record)

    if not rows:
        raise ValueError("No valid records remain after latitude/longitude validation.")
    return rows, dropped


def demo_records() -> list[dict[str, Any]]:
    """A small synthetic US sample so the dashboard works before uploading real data."""
    sample = [
        ("2025-01-02T07:35:00",39.1031,-84.5120,"OH","Cincinnati",3,"Light Rain",35,91,4,28,0.4,1,0,1,"Night"),
        ("2025-01-02T08:10:00",39.0997,-84.5150,"OH","Cincinnati",2,"Cloudy",38,82,7,8,0,0,1,1,"Day"),
        ("2025-01-03T17:45:00",40.7128,-74.0060,"NY","New York",4,"Heavy Rain",44,98,1,31,0.7,1,0,0,"Night"),
        ("2025-01-04T14:25:00",34.0522,-118.2437,"CA","Los Angeles",2,"Clear",71,42,10,4,0,0,0,1,"Day"),
        ("2025-01-05T06:50:00",41.8781,-87.6298,"IL","Chicago",3,"Snow",24,87,2,35,0.2,1,1,0,"Night"),
        ("2025-01-06T12:05:00",29.7604,-95.3698,"TX","Houston",2,"Clear",77,55,10,6,0,0,1,1,"Day"),
        ("2025-01-07T19:30:00",47.6062,-122.3321,"WA","Seattle",3,"Fog",40,96,2,12,0,1,0,0,"Night"),
        ("2025-01-08T10:15:00",33.4484,-112.0740,"AZ","Phoenix",2,"Clear",82,28,10,3,0,0,0,1,"Day"),
        ("2025-01-09T23:10:00",25.7617,-80.1918,"FL","Miami",4,"Heavy Rain",76,95,2,29,1.1,1,1,0,"Night"),
        ("2025-01-10T16:20:00",39.9612,-82.9988,"OH","Columbus",3,"Overcast",32,70,6,14,0.1,0,1,1,"Day"),
        ("2025-01-11T05:55:00",44.9778,-93.2650,"MN","Minneapolis",4,"Snow",12,88,1,42,0.8,1,1,0,"Night"),
        ("2025-01-12T13:05:00",36.1627,-86.7816,"TN","Nashville",2,"Clear",67,47,10,5,0,0,0,1,"Day"),
        ("2025-02-03T21:20:00",39.7392,-104.9903,"CO","Denver",3,"Freezing Rain",28,92,2,22,0.9,1,0,0,"Night"),
        ("2025-02-04T09:12:00",42.3601,-71.0589,"MA","Boston",2,"Light Rain",46,88,5,18,0.2,0,1,1,"Day"),
        ("2025-02-08T18:40:00",32.7767,-96.7970,"TX","Dallas",3,"Thunderstorm",73,94,3,33,1.4,1,0,0,"Night"),
        ("2025-02-11T11:30:00",45.5152,-122.6784,"OR","Portland",2,"Overcast",51,79,6,7,0,1,0,1,"Day"),
        ("2025-02-14T02:15:00",39.9526,-75.1652,"PA","Philadelphia",4,"Fog",31,98,1,9,0,1,0,0,"Night"),
        ("2025-02-19T15:55:00",33.7490,-84.3880,"GA","Atlanta",2,"Clear",69,52,10,12,0,0,1,1,"Day"),
        ("2025-02-23T06:05:00",36.1699,-115.1398,"NV","Las Vegas",3,"Dust",48,30,4,26,0,0,0,0,"Night"),
        ("2025-02-28T20:45:00",39.2904,-76.6122,"MD","Baltimore",3,"Rain",49,93,4,20,0.3,1,1,0,"Night"),
    ]
    columns = [
        "start_time","start_lat","start_lng","state","city","severity","weather_condition",
        "temperature_f","humidity","visibility_mi","wind_speed_mph","precipitation_in",
        "junction","traffic_signal","crossing","sunrise_sunset",
    ]
    out: list[dict[str, Any]] = []
    for values in sample:
        record = dict(zip(columns, values))
        for flag in ROAD_FLAGS:
            record[flag] = bool(record[flag])
        for field in NUMERIC_FIELDS:
            record[field] = float(record[field]) if record[field] is not None else None
        score, band, explanation = score_record(record)
        record.update({"risk_score": score, "risk_band": band, "explanation": explanation})
        out.append(record)
    return out


def quality_report(records: list[dict[str, Any]], dropped_rows: int = 0) -> dict[str, Any]:
    fields = [
        "start_time","start_lat","start_lng","state","city","severity","weather_condition",
        "temperature_f","humidity","visibility_mi","wind_speed_mph","precipitation_in",
        "sunrise_sunset",
    ]
    total = len(records)
    missing = {
        field: sum(1 for row in records if row.get(field) is None or row.get(field) == "Unknown")
        for field in fields
    }
    return {
        "rows": total,
        "rows_dropped_invalid_coordinates": dropped_rows,
        "fields": [
            {"field": field, "missing": count, "missing_percent": round(count / total * 100, 1) if total else 0}
            for field, count in missing.items()
        ],
    }

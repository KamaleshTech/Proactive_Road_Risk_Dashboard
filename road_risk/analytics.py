"""Data validation and explainable historical-risk heuristics."""
from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

REQUIRED_COORDS = ("Start_Lat", "Start_Lng")
NUMERIC_COLUMNS = (
    "Severity", "Temperature(F)", "Wind_Chill(F)", "Humidity(%)",
    "Pressure(in)", "Visibility(mi)", "Wind_Speed(mph)", "Precipitation(in)",
)
DATE_COLUMNS = ("Start_Time", "End_Time", "Weather_Timestamp")
ROAD_FLAGS = (
    "Amenity", "Bump", "Crossing", "Give_Way", "Junction", "No_Exit",
    "Railway", "Roundabout", "Station", "Stop", "Traffic_Calming",
    "Traffic_Signal", "Turning_Loop",
)


@dataclass
class DataReport:
    rows_in: int
    rows_out: int
    dropped_bad_coordinates: int
    missing_values: dict[str, int]
    warnings: list[str]


def demo_data() -> pd.DataFrame:
    """Small synthetic dataset, clearly labelled for UI demonstration only."""
    rows = [
        ("2023-01-03 07:35",39.1031,-84.5120,"OH","Cincinnati",3,"Light Rain",35,91,4,2.5,True,False,True,"Night"),
        ("2023-01-03 08:10",39.0997,-84.5150,"OH","Cincinnati",2,"Cloudy",38,82,7,1.5,False,True,True,"Day"),
        ("2023-01-04 17:45",40.7128,-74.0060,"NY","New York",4,"Heavy Rain",44,98,1,22,True,False,False,"Night"),
        ("2023-01-05 14:25",34.0522,-118.2437,"CA","Los Angeles",2,"Clear",71,42,10,4,False,False,True,"Day"),
        ("2023-01-06 06:50",41.8781,-87.6298,"IL","Chicago",3,"Snow",24,87,2,14,True,True,False,"Night"),
        ("2023-01-07 12:05",29.7604,-95.3698,"TX","Houston",2,"Clear",77,55,10,6,False,True,True,"Day"),
        ("2023-01-08 19:30",47.6062,-122.3321,"WA","Seattle",3,"Fog",40,96,2,3,True,False,False,"Night"),
        ("2023-01-09 10:15",33.4484,-112.0740,"AZ","Phoenix",2,"Clear",82,28,10,3,False,False,True,"Day"),
        ("2023-01-10 23:10",25.7617,-80.1918,"FL","Miami",4,"Heavy Rain",76,95,2,18,True,True,False,"Night"),
        ("2023-01-11 16:20",39.9612,-82.9988,"OH","Columbus",3,"Overcast",32,70,6,8,False,True,True,"Day"),
        ("2023-01-12 05:55",44.9778,-93.2650,"MN","Minneapolis",4,"Snow",12,88,1,20,True,True,False,"Night"),
        ("2023-01-13 13:05",36.1627,-86.7816,"TN","Nashville",2,"Clear",67,47,10,5,False,False,True,"Day"),
    ]
    columns = [
        "Start_Time","Start_Lat","Start_Lng","State","City","Severity",
        "Weather_Condition","Temperature(F)","Humidity(%)","Visibility(mi)",
        "Wind_Speed(mph)","Junction","Traffic_Signal","Crossing","Sunrise_Sunset",
    ]
    data = pd.DataFrame(rows, columns=columns)
    data["Country"] = "US"
    return data


def normalize_dataframe(raw: pd.DataFrame) -> tuple[pd.DataFrame, DataReport]:
    """Copy, validate, and normalize a CSV DataFrame."""
    if not isinstance(raw, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")
    if raw.empty:
        raise ValueError("The uploaded CSV has no rows.")
    data = raw.copy()
    data.columns = [str(col).strip() for col in data.columns]
    if data.columns.duplicated().any():
        duplicate_names = data.columns[data.columns.duplicated()].tolist()
        raise ValueError(f"Duplicate column names detected: {duplicate_names}")
    missing_coords = [name for name in REQUIRED_COORDS if name not in data.columns]
    if missing_coords:
        raise ValueError(
            "CSV is missing required coordinate columns: "
            + ", ".join(missing_coords) + ". Expected Start_Lat and Start_Lng."
        )

    rows_in = len(data)
    for col in (*NUMERIC_COLUMNS, *REQUIRED_COORDS):
        if col in data:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    for col in DATE_COLUMNS:
        if col in data:
            data[col] = pd.to_datetime(data[col], errors="coerce", format="mixed")

    invalid = (
        data["Start_Lat"].isna()
        | data["Start_Lng"].isna()
        | ~data["Start_Lat"].between(-90, 90)
        | ~data["Start_Lng"].between(-180, 180)
    )
    dropped = int(invalid.sum())
    data = data.loc[~invalid].copy()
    if data.empty:
        raise ValueError("No valid rows remain after validating latitude/longitude.")

    warnings: list[str] = []
    outside = ~data["Start_Lat"].between(24, 50) | ~data["Start_Lng"].between(-126, -66)
    if outside.any():
        warnings.append(
            f"{int(outside.sum()):,} rows lie outside the approximate continental-US extent; retained."
        )
    if dropped:
        warnings.append(f"Dropped {dropped:,} rows with missing or invalid start coordinates.")
    missing_values = {str(k): int(v) for k, v in data.isna().sum().items() if v > 0}
    if missing_values:
        warnings.append("Missing values detected; each chart uses available values for its own fields.")
    return data.reset_index(drop=True), DataReport(
        rows_in, len(data), dropped, missing_values, warnings
    )


def add_historical_indicator(data: pd.DataFrame) -> pd.DataFrame:
    """Return an explanatory rule-based score, not a calibrated crash probability."""
    out = data.copy()
    score = pd.Series(0.0, index=out.index)
    explanations: dict[int, list[str]] = {idx: [] for idx in out.index}

    def add(mask: pd.Series, points: int, reason: str) -> None:
        valid = mask.reindex(out.index).fillna(False).astype(bool)
        score.loc[valid] += points
        for idx in out.index[valid]:
            explanations[idx].append(reason)

    if "Visibility(mi)" in out:
        visibility = pd.to_numeric(out["Visibility(mi)"], errors="coerce")
        add(visibility <= 3, 25, "Low visibility (≤3 mi)")
        add((visibility > 3) & (visibility <= 5), 12, "Reduced visibility (3–5 mi)")
    if "Weather_Condition" in out:
        weather = out["Weather_Condition"].astype("string").str.lower()
        severe = weather.str.contains(r"heavy rain|thunder|snow|sleet|ice|freezing|fog", na=False)
        add(severe, 25, "Severe weather label")
        wet = weather.str.contains(r"rain|drizzle|overcast", na=False) & ~severe
        add(wet, 10, "Wet or overcast weather label")
    if "Precipitation(in)" in out:
        precip = pd.to_numeric(out["Precipitation(in)"], errors="coerce")
        add((precip >= 0.25) & (precip < 10), 15, "Elevated precipitation")
    if "Wind_Speed(mph)" in out:
        wind = pd.to_numeric(out["Wind_Speed(mph)"], errors="coerce")
        add((wind >= 25) & (wind <= 150), 10, "High wind speed")
    if "Humidity(%)" in out:
        humidity = pd.to_numeric(out["Humidity(%)"], errors="coerce")
        add(humidity >= 90, 8, "Very high humidity")
    if "Sunrise_Sunset" in out:
        add(out["Sunrise_Sunset"].astype("string").str.lower().eq("night"), 8, "Night-time record")
    for col in ROAD_FLAGS:
        if col not in out:
            continue
        value = out[col]
        if value.dtype == object or str(value.dtype).startswith("string"):
            enabled = value.astype("string").str.lower().isin(["true", "1", "yes", "y"])
        else:
            enabled = value.fillna(False).astype(bool)
        add(enabled, 5, f"Road-context flag: {col}")

    out["Historical_Risk_Indicator"] = score.clip(0, 100).round().astype(int)
    out["Indicator_Band"] = pd.cut(
        out["Historical_Risk_Indicator"],
        bins=[-1, 24, 49, 74, 100],
        labels=["Low", "Guarded", "Elevated", "High"],
    ).astype("string")
    out["Indicator_Explanation"] = [
        "; ".join(explanations[idx]) if explanations[idx]
        else "No configured risk indicators were detected"
        for idx in out.index
    ]
    return out


def quality_summary(data: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "Column": [str(col) for col in data.columns],
        "Data type": [str(data[col].dtype) for col in data.columns],
        "Missing values": [int(data[col].isna().sum()) for col in data.columns],
        "Missing (%)": [round(float(data[col].isna().mean() * 100), 2) for col in data.columns],
    }).sort_values(["Missing (%)", "Column"], ascending=[False, True]).reset_index(drop=True)


def filtered_records(data: pd.DataFrame, states: list[str], severities: list[int], bands: list[str]) -> pd.DataFrame:
    result = data.copy()
    if states and "State" in result:
        result = result[result["State"].astype("string").isin(states)]
    if severities and "Severity" in result:
        result = result[pd.to_numeric(result["Severity"], errors="coerce").isin(severities)]
    if bands and "Indicator_Band" in result:
        result = result[result["Indicator_Band"].astype("string").isin(bands)]
    return result.reset_index(drop=True)

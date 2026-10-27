"""FastAPI application for the Proactive Road Risk Dashboard."""
from __future__ import annotations

from collections import Counter
from io import BytesIO
import os
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from backend.analytics import MAX_IMPORT_ROWS, normalize_dataframe, quality_report
from backend.storage import (
    get_metadata,
    get_records,
    initialize_database,
    replace_dataset,
    reset_demo_dataset,
)

APP_VERSION = "2.0.0"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

app = FastAPI(
    title="Proactive Road Risk API",
    description=(
        "Historical road accident analytics and explainable heuristic indicators. "
        "This service does not claim to predict future crashes."
    ),
    version=APP_VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "proactive-road-risk-api", "version": APP_VERSION}


@app.get("/api/meta")
def metadata() -> dict[str, Any]:
    return get_metadata()


def _filters(
    records: list[dict[str, Any]],
    state: str | None,
    severity: int | None,
    band: str | None,
    search: str | None,
) -> list[dict[str, Any]]:
    result = records
    if state:
        result = [row for row in result if row["state"] == state]
    if severity is not None:
        result = [row for row in result if row["severity"] == severity]
    if band:
        result = [row for row in result if row["risk_band"] == band]
    if search:
        needle = search.strip().lower()
        if needle:
            result = [
                row for row in result
                if needle in str(row.get("city", "")).lower()
                or needle in str(row.get("state", "")).lower()
                or needle in str(row.get("weather_condition", "")).lower()
                or needle in str(row.get("explanation", "")).lower()
            ]
    return result


def _dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    if not df.empty and "start_time" in df:
        df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce", format="mixed")
    return df


@app.get("/api/options")
def options() -> dict[str, Any]:
    records = get_records()
    return {
        "states": sorted({row["state"] for row in records if row.get("state") and row["state"] != "Unknown"}),
        "severities": sorted({row["severity"] for row in records if row.get("severity") is not None}),
        "bands": ["Low", "Guarded", "Elevated", "High"],
    }


@app.get("/api/dashboard")
def dashboard(
    state: str | None = None,
    severity: int | None = Query(default=None, ge=1, le=4),
    band: str | None = Query(default=None, pattern="^(Low|Guarded|Elevated|High)$"),
    search: str | None = Query(default=None, max_length=120),
) -> dict[str, Any]:
    all_records = get_records()
    records = _filters(all_records, state, severity, band, search)
    df = _dataframe(records)

    total = len(records)
    band_order = ["Low", "Guarded", "Elevated", "High"]
    bands = Counter(row["risk_band"] for row in records)
    severities = Counter(str(row["severity"]) for row in records if row.get("severity") is not None)
    by_state = Counter(row["state"] for row in records if row.get("state") and row["state"] != "Unknown")
    by_weather = Counter(row["weather_condition"] for row in records if row.get("weather_condition"))
    monthly: list[dict[str, Any]] = []
    hourly: list[dict[str, Any]] = []
    if not df.empty and df["start_time"].notna().any():
        dated = df.dropna(subset=["start_time"]).copy()
        dated["month"] = dated["start_time"].dt.to_period("M").astype(str)
        monthly = [
            {"month": str(row["month"]), "records": int(row["records"])}
            for _, row in dated.groupby("month").size().rename("records").reset_index().sort_values("month").tail(36).iterrows()
        ]
        dated["hour"] = dated["start_time"].dt.hour
        hourly = [
            {"hour": int(row["hour"]), "records": int(row["records"])}
            for _, row in dated.groupby("hour").size().rename("records").reset_index().sort_values("hour").iterrows()
        ]

    sorted_records = sorted(
        records,
        key=lambda row: (
            row.get("start_time") or "",
            row.get("risk_score", 0),
        ),
        reverse=True,
    )
    map_source = sorted_records
    if len(map_source) > 2500:
        # Deterministic evenly-spaced sample keeps browser rendering responsive.
        stride = max(1, len(map_source) // 2500)
        map_source = map_source[::stride][:2500]
    map_points = [
        {
            "id": row.get("id"),
            "lat": row["start_lat"],
            "lng": row["start_lng"],
            "city": row["city"],
            "state": row["state"],
            "risk_band": row["risk_band"],
            "risk_score": row["risk_score"],
            "severity": row.get("severity"),
        }
        for row in map_source
    ]

    scored = [row["risk_score"] for row in records]
    meta = get_metadata()
    return {
        "meta": meta,
        "summary": {
            "records": total,
            "mean_indicator": round(sum(scored) / total, 1) if total else 0,
            "elevated_high": sum(1 for row in records if row["risk_band"] in ("Elevated", "High")),
            "high_records": sum(1 for row in records if row["risk_band"] == "High"),
            "demo_mode": meta["is_demo"],
        },
        "risk_bands": [{"band": key, "records": int(bands.get(key, 0))} for key in band_order],
        "severity": [{"severity": key, "records": int(severities.get(key, 0))} for key in sorted(severities, key=int)],
        "by_state": [{"state": key, "records": value} for key, value in by_state.most_common(12)],
        "by_weather": [{"weather": key, "records": value} for key, value in by_weather.most_common(10)],
        "monthly": monthly,
        "hourly": hourly,
        "map_points": map_points,
        "quality": quality_report(records, meta["dropped_rows"]),
        "top_records": sorted(records, key=lambda row: row["risk_score"], reverse=True)[:8],
    }


@app.get("/api/records")
def records_page(
    state: str | None = None,
    severity: int | None = Query(default=None, ge=1, le=4),
    band: str | None = Query(default=None, pattern="^(Low|Guarded|Elevated|High)$"),
    search: str | None = Query(default=None, max_length=120),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict[str, Any]:
    records = _filters(get_records(), state, severity, band, search)
    records.sort(key=lambda row: row.get("start_time") or "", reverse=True)
    return {"total": len(records), "offset": offset, "limit": limit, "items": records[offset:offset + limit]}


@app.get("/api/quality")
def quality(
    state: str | None = None,
    severity: int | None = Query(default=None, ge=1, le=4),
    band: str | None = Query(default=None, pattern="^(Low|Guarded|Elevated|High)$"),
    search: str | None = Query(default=None, max_length=120),
) -> dict[str, Any]:
    meta = get_metadata()
    records = _filters(get_records(), state, severity, band, search)
    return {
        "dataset": meta,
        "report": quality_report(records, meta["dropped_rows"]),
    }


@app.get("/api/export.csv")
def export_csv(
    state: str | None = None,
    severity: int | None = Query(default=None, ge=1, le=4),
    band: str | None = Query(default=None, pattern="^(Low|Guarded|Elevated|High)$"),
    search: str | None = Query(default=None, max_length=120),
) -> StreamingResponse:
    records = _filters(get_records(), state, severity, band, search)
    df = pd.DataFrame(records)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="road-risk-records.csv"'},
    )


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)) -> dict[str, Any]:
    name = (file.filename or "upload.csv").strip()
    if not name.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a CSV file.")
    raw_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 25 MB. Upload a smaller CSV sample.")
    try:
        raw_df = pd.read_csv(BytesIO(raw_bytes), low_memory=False)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read CSV: {exc}") from exc
    if len(raw_df) > MAX_IMPORT_ROWS:
        raise HTTPException(
            status_code=413,
            detail=f"CSV has {len(raw_df):,} rows; this showcase accepts up to {MAX_IMPORT_ROWS:,} rows per upload. Upload a smaller representative sample.",
        )
    try:
        rows, dropped = normalize_dataframe(raw_df)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    replace_dataset(rows, name=name[:180], is_demo=False, dropped_rows=dropped)
    return {"message": "Dataset imported successfully.", "metadata": get_metadata()}


@app.post("/api/demo/reset")
def reset_demo() -> dict[str, Any]:
    reset_demo_dataset()
    return {"message": "Synthetic sample restored.", "metadata": get_metadata()}


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Any, exc: Exception) -> Response:
    # Never expose raw exception details to clients; they may contain paths or input data.
    import logging
    logging.getLogger("road_risk.api").exception("Unexpected API error")
    return Response(
        content='{"detail":"Unexpected server error. Check the backend logs."}',
        status_code=500,
        media_type="application/json",
    )

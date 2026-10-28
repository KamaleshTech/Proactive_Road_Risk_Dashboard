"""SQLite persistence for the dashboard's active dataset."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

from backend.analytics import demo_records

ROOT = Path(__file__).resolve().parents[1]
RECORD_COLUMNS = (
    "start_time", "start_lat", "start_lng", "state", "city", "severity",
    "weather_condition", "temperature_f", "humidity", "visibility_mi",
    "wind_speed_mph", "precipitation_in", "junction", "traffic_signal",
    "crossing", "sunrise_sunset", "risk_score", "risk_band", "explanation",
)


def database_path() -> Path:
    configured = os.getenv("DATABASE_PATH", "data/road_risk.db")
    path = Path(configured)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(database_path(), timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 15000")
    return connection


def initialize_database() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              start_time TEXT,
              start_lat REAL NOT NULL,
              start_lng REAL NOT NULL,
              state TEXT NOT NULL,
              city TEXT NOT NULL,
              severity INTEGER,
              weather_condition TEXT NOT NULL,
              temperature_f REAL,
              humidity REAL,
              visibility_mi REAL,
              wind_speed_mph REAL,
              precipitation_in REAL,
              junction INTEGER NOT NULL DEFAULT 0,
              traffic_signal INTEGER NOT NULL DEFAULT 0,
              crossing INTEGER NOT NULL DEFAULT 0,
              sunrise_sunset TEXT NOT NULL,
              risk_score INTEGER NOT NULL,
              risk_band TEXT NOT NULL,
              explanation TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS dataset_meta (
              id INTEGER PRIMARY KEY CHECK (id = 1),
              name TEXT NOT NULL,
              is_demo INTEGER NOT NULL,
              row_count INTEGER NOT NULL,
              dropped_rows INTEGER NOT NULL DEFAULT 0,
              updated_at TEXT NOT NULL
            )
            """
        )
        count = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        meta = connection.execute("SELECT id FROM dataset_meta WHERE id = 1").fetchone()
        if count == 0 or meta is None:
            seed = demo_records()
            _replace_dataset_in_connection(
                connection, seed, name="Synthetic showcase sample", is_demo=True, dropped_rows=0
            )


def _replace_dataset_in_connection(
    connection: sqlite3.Connection,
    records: list[dict[str, Any]],
    *,
    name: str,
    is_demo: bool,
    dropped_rows: int,
) -> None:
    connection.execute("DELETE FROM records")
    placeholders = ", ".join("?" for _ in range(len(RECORD_COLUMNS)))
    sql = f"INSERT INTO records ({', '.join(RECORD_COLUMNS)}) VALUES ({placeholders})"
    values = []
    for record in records:
        values.append(tuple(
            int(record.get(col, False)) if col in {"junction", "traffic_signal", "crossing"}
            else record.get(col)
            for col in RECORD_COLUMNS
        ))
    connection.executemany(sql, values)
    now = datetime.now(timezone.utc).isoformat()
    connection.execute(
        """
        INSERT INTO dataset_meta (id, name, is_demo, row_count, dropped_rows, updated_at)
        VALUES (1, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          name=excluded.name,
          is_demo=excluded.is_demo,
          row_count=excluded.row_count,
          dropped_rows=excluded.dropped_rows,
          updated_at=excluded.updated_at
        """,
        (name, 1 if is_demo else 0, len(records), dropped_rows, now),
    )


def replace_dataset(
    records: list[dict[str, Any]],
    *,
    name: str,
    is_demo: bool = False,
    dropped_rows: int = 0,
) -> None:
    initialize_database()
    with connect() as connection:
        with connection:
            _replace_dataset_in_connection(
                connection, records, name=name, is_demo=is_demo, dropped_rows=dropped_rows
            )


def reset_demo_dataset() -> None:
    replace_dataset(demo_records(), name="Synthetic showcase sample", is_demo=True, dropped_rows=0)


def get_metadata() -> dict[str, Any]:
    initialize_database()
    with connect() as connection:
        row = connection.execute("SELECT * FROM dataset_meta WHERE id = 1").fetchone()
    return {
        "name": row["name"],
        "is_demo": bool(row["is_demo"]),
        "row_count": int(row["row_count"]),
        "dropped_rows": int(row["dropped_rows"]),
        "updated_at": row["updated_at"],
    }


def get_records() -> list[dict[str, Any]]:
    initialize_database()
    with connect() as connection:
        rows = connection.execute(
            "SELECT * FROM records ORDER BY COALESCE(start_time, '') DESC, id DESC"
        ).fetchall()
    return [dict(row) for row in rows]

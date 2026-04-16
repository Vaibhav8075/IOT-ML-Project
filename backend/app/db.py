import json
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "iot_fire.db"


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                zone_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                temperature_c REAL NOT NULL,
                humidity_pct REAL NOT NULL,
                pm25 REAL NOT NULL,
                co_adc REAL NOT NULL,
                flame_channels_json TEXT NOT NULL,
                pir_motion INTEGER NOT NULL,
                ldr_raw REAL NOT NULL,
                ldr_flicker REAL NOT NULL,
                predicted_label TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def insert_telemetry(payload, predicted_label, confidence):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO telemetry (
                device_id,
                zone_id,
                timestamp,
                temperature_c,
                humidity_pct,
                pm25,
                co_adc,
                flame_channels_json,
                pir_motion,
                ldr_raw,
                ldr_flicker,
                predicted_label,
                confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.device_id,
                payload.zone_id,
                payload.timestamp.isoformat(),
                payload.temperature_c,
                payload.humidity_pct,
                payload.pm25,
                payload.co_adc,
                json.dumps(payload.flame_channels),
                payload.pir_motion,
                payload.ldr_raw,
                payload.ldr_flicker,
                predicted_label,
                confidence,
            ),
        )
        return cursor.lastrowid


def fetch_latest_telemetry(limit=1):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM telemetry
            ORDER BY timestamp DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_latest_per_zone():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT t.*
            FROM telemetry t
            INNER JOIN (
                SELECT zone_id, MAX(timestamp) AS max_timestamp
                FROM telemetry
                GROUP BY zone_id
            ) latest
            ON t.zone_id = latest.zone_id AND t.timestamp = latest.max_timestamp
            ORDER BY t.zone_id
            """
        ).fetchall()
    return [dict(row) for row in rows]

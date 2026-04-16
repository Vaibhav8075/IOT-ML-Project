import json

from fastapi import FastAPI

from .db import fetch_latest_per_zone, fetch_latest_telemetry, init_db, insert_telemetry
from .schemas import TelemetryIn, TelemetryOut, ZoneStatusOut


app = FastAPI(title="IoT Fire Detection Backend", version="0.1.0")


def infer_label(payload: TelemetryIn):
    flame_hits = sum(payload.flame_channels)

    if (
        flame_hits >= 1
        and payload.temperature_c >= 70
        and (payload.pm25 >= 150 or payload.co_adc >= 1200 or payload.ldr_flicker >= 120)
    ):
        return "fire", 0.94

    if (
        payload.temperature_c >= 45
        or payload.pm25 >= 75
        or payload.co_adc >= 700
        or payload.ldr_flicker >= 80
    ):
        return "warning", 0.74

    return "normal", 0.91


def normalize_row(row):
    flame_channels = json.loads(row["flame_channels_json"])
    return {
        "id": row["id"],
        "device_id": row["device_id"],
        "zone_id": row["zone_id"],
        "timestamp": row["timestamp"],
        "temperature_c": row["temperature_c"],
        "humidity_pct": row["humidity_pct"],
        "pm25": row["pm25"],
        "co_adc": row["co_adc"],
        "flame_channels": flame_channels,
        "pir_motion": row["pir_motion"],
        "ldr_raw": row["ldr_raw"],
        "ldr_flicker": row["ldr_flicker"],
        "predicted_label": row["predicted_label"],
        "confidence": row["confidence"],
    }


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/telemetry")
def ingest_telemetry(payload: TelemetryIn):
    predicted_label, confidence = infer_label(payload)
    row_id = insert_telemetry(payload, predicted_label, confidence)
    return {
        "message": "telemetry stored",
        "id": row_id,
        "predicted_label": predicted_label,
        "confidence": confidence,
    }


@app.get("/telemetry/latest", response_model=list[TelemetryOut])
def latest_telemetry(limit: int = 20):
    limit = max(1, min(limit, 200))
    return [normalize_row(row) for row in fetch_latest_telemetry(limit=limit)]


@app.get("/zones/status", response_model=list[ZoneStatusOut])
def zone_status():
    rows = []
    for row in fetch_latest_per_zone():
        rows.append(
            {
                "zone_id": row["zone_id"],
                "device_id": row["device_id"],
                "timestamp": row["timestamp"],
                "predicted_label": row["predicted_label"],
                "confidence": row["confidence"],
                "temperature_c": row["temperature_c"],
                "humidity_pct": row["humidity_pct"],
                "pm25": row["pm25"],
                "co_adc": row["co_adc"],
            }
        )
    return rows

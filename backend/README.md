# Backend

## Run

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the API from the repo root:

```powershell
uvicorn backend.app.main:app --reload
```

## Endpoints

- `GET /health`
- `POST /telemetry`
- `GET /telemetry/latest`
- `GET /zones/status`

## Example Payload

```json
{
  "device_id": "esp32-lab-01",
  "zone_id": "lab-room",
  "timestamp": "2026-04-15T10:30:00Z",
  "temperature_c": 34.8,
  "humidity_pct": 62.4,
  "pm25": 118.0,
  "co_adc": 740,
  "flame_channels": [0, 0, 1, 0, 0],
  "pir_motion": 1,
  "ldr_raw": 820,
  "ldr_flicker": 44.5
}
```

## Notes

- This is the first backend slice, not the final architecture.
- Inference is currently rule-based so the API can be exercised immediately.
- The next step is to connect the existing dashboard to these endpoints.

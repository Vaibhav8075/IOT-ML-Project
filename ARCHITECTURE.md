# Software Architecture

## Goal

Move the current proof-of-concept from:

- synthetic data generation
- local Python model training
- CSV-based dashboard demo

to a deployable IoT fire detection platform with:

- real ESP32-S3 device integration
- a live digital twin layer
- production-grade machine learning workflow
- alerting and actuator control

## Current State

The repository currently implements:

- synthetic training data generation
- a Random Forest classifier
- a simulated logger that writes to CSV
- a Dash dashboard that reads recent rows from CSV

This is a good demo base, but it does not yet include:

- real device ingestion
- a backend API or message broker
- persistent storage
- a true digital twin model
- real-world ML data collection and retraining pipeline
- production alerting or actuator orchestration

## Target Architecture

### 1. Edge Device Layer

Hardware:

- ESP32-S3-DevKitC-1
- PMS7003
- MQ-7
- 5-channel flame sensor
- DHT22
- PIR
- LDR
- buzzer
- relay
- SIM800L

Software responsibilities:

- sensor polling
- local preprocessing and sanity checks
- timestamping
- packaging telemetry
- publishing telemetry over Wi-Fi
- local fail-safe rules for buzzer and relay
- optional on-device inference later if TinyML is adopted

Recommended protocol:

- MQTT for telemetry and commands

Fallback:

- HTTP POST to backend if MQTT is not possible during the first phase

### 2. Backend Ingestion Layer

Responsibilities:

- receive telemetry from devices
- validate payload schema
- persist telemetry
- expose historical and live data to the frontend
- run alert workflows
- send command messages back to devices

Recommended components:

- Python FastAPI service
- MQTT broker such as Mosquitto
- PostgreSQL for telemetry and alerts
- Redis optional for real-time pub/sub and caching

Core backend modules:

- device registration
- telemetry ingestion
- inference service integration
- alert rules
- actuator command dispatch
- audit/event logging

### 3. ML Inference and Training Layer

Responsibilities:

- infer state: `normal`, `warning`, `fire`
- store confidence score and model version
- maintain training datasets
- retrain on labeled real-world data
- evaluate false positives and false negatives

Recommended ML progression:

Phase 1:

- keep Random Forest as the first baseline model

Phase 2:

- engineer time-window features
- compare Random Forest, XGBoost, LightGBM, and simple temporal models

Phase 3:

- consider TinyML deployment on ESP32-S3 only after server-side model quality is stable

ML service outputs should include:

- predicted class
- class probabilities
- model version
- features used
- explanation or top contributing signals if available

### 4. Digital Twin Layer

The digital twin should become more than a chart dashboard.

Target capabilities:

- map devices to physical zones or rooms
- show live zone status
- highlight warnings and fire events spatially
- show device health and last seen time
- replay timeline of incident evolution
- visualize alert propagation and actuator response

Recommended structure:

- `building`
- `floors`
- `zones`
- `devices`
- `sensors`
- `events`

The existing `building_3d_model.json` can become the seed for:

- zone geometry metadata
- sensor placement metadata
- floor or room identifiers

### 5. Frontend Layer

Current Dash dashboard can be extended in stages, but a future React frontend may be easier for a richer digital twin.

Minimum frontend responsibilities:

- live telemetry panel
- per-zone status cards
- alert timeline
- device health
- actuator status
- historical trends

Nice-to-have:

- 2D floor plan first
- 3D visualization later

Important recommendation:

Start with a 2D zone map before investing in full 3D rendering. That will still count as a digital twin if it mirrors the physical layout and live system state.

### 6. Alerting and Response Layer

When `fire` is detected:

- activate local buzzer
- trigger relay for fan or pump
- send SMS through SIM800L
- create alert event in backend
- update digital twin zone state to `fire`

When `warning` is detected:

- show dashboard warning
- optionally send pre-alert notification
- log event for later labeling and review

### 7. Data Storage

Minimum tables or collections:

- `devices`
- `telemetry`
- `predictions`
- `alerts`
- `commands`
- `zones`
- `incidents`

Telemetry should not be stored in CSV for production.

## Recommended Repository Direction

Suggested future repo structure:

```text
firmware/
  esp32/
backend/
  app/
    api/
    models/
    services/
    schemas/
    workers/
frontend/
  dashboard/
ml/
  notebooks/
  training/
  inference/
  data/
docs/
```

## Recommended First Software Deliverables

1. Replace CSV-based logging with a backend ingestion API.
2. Add a telemetry schema shared between device and backend.
3. Store live sensor readings in a database.
4. Feed the dashboard from the backend instead of directly from CSV.
5. Add zone metadata so the dashboard can show where an event is happening.
6. Start collecting real hardware data for model retraining.

## Definition Of Done For The Three Big Missing Pieces

### Real device-to-software integration

Done when:

- ESP32 sends live telemetry to backend
- backend stores readings
- dashboard shows live hardware data
- backend can send commands for buzzer or relay actions

### True digital twin layer

Done when:

- devices are placed in zones
- zones change status from live inference results
- operator can see incident location and history
- the twin reflects both telemetry and actuator state

### Production-grade ML with real data

Done when:

- real sensor dataset exists
- labels are reviewed and stored
- reproducible training pipeline exists
- model versioning and evaluation metrics exist
- live inference runs against real telemetry

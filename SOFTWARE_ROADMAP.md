# Software Roadmap

## Goal

This roadmap breaks the project into practical software milestones so the current repo can grow into a full IoT + ML + digital twin platform.

## Phase 0: Stabilize The Current Demo

Status: partially complete

Already present:

- synthetic data generator
- baseline model
- simulated logging
- dashboard

Still needed:

- dependency manifest such as `requirements.txt`
- run instructions
- consistent dataset locations and file naming
- cleanup of duplicate or mismatched data files
- basic smoke tests for scripts

Deliverables:

- `requirements.txt`
- updated `README.md`
- one canonical data directory
- one canonical runtime log location

## Phase 1: Real Device Integration

Objective:

Replace simulator-first workflow with real ESP32 telemetry.

Tasks:

1. Create a telemetry schema.
2. Build a backend ingestion API or MQTT consumer.
3. Write ESP32 firmware to publish readings.
4. Add device registration and heartbeat tracking.
5. Store readings in a database.

Suggested payload:

```json
{
  "device_id": "esp32-lab-01",
  "timestamp": "2026-04-15T10:30:00Z",
  "zone_id": "kitchen-01",
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

Done when:

- one ESP32 can stream live data into the software stack
- data is visible in dashboard without CSV files

## Phase 2: Backend And Persistence

Objective:

Add a proper service layer between devices, ML, and UI.

Tasks:

1. Create FastAPI backend.
2. Add PostgreSQL models for devices, telemetry, predictions, alerts, and commands.
3. Add live endpoints:
   - latest telemetry
   - telemetry history
   - zone status
   - active alerts
4. Add MQTT or WebSocket push for real-time updates.
5. Add an incident log.

Done when:

- backend becomes the source of truth
- frontend no longer reads directly from local files

## Phase 3: Digital Twin V1

Objective:

Turn the dashboard into a physical-system representation.

Tasks:

1. Define building, floor, zone, and device metadata.
2. Create a 2D floor map with live zone colors.
3. Show sensor placement in each zone.
4. Highlight warning and fire locations.
5. Show device health and last seen status.
6. Add event timeline and replay.

Important note:

A strong 2D zone-based twin is a better first target than trying to jump straight to full 3D.

Done when:

- operator can identify where an event is happening and what devices are involved

## Phase 4: ML With Real Data

Objective:

Move from synthetic-model demo to reliable real-world inference.

Tasks:

1. Collect real telemetry from controlled scenarios.
2. Label sessions as `normal`, `warning`, or `fire`.
3. Create dataset versioning.
4. Build preprocessing and feature engineering pipeline.
5. Compare baseline models.
6. Track class-specific metrics:
   - recall for `fire`
   - precision for `warning`
   - false alarm rate
   - missed detection rate
7. Save model version metadata.

Recommended features:

- rolling averages
- rolling max
- rate of change
- PM and CO trend deltas
- flame channel aggregation
- flicker variance over a time window
- occupancy context from PIR

Done when:

- model is trained on real device data
- evaluation is reproducible
- live predictions include confidence and model version

## Phase 5: Alerting And Automation

Objective:

Connect inference to real response actions.

Tasks:

1. Trigger buzzer on confirmed fire.
2. Trigger relay for fan or pump.
3. Send SMS using SIM800L.
4. Add retry and acknowledgment logic.
5. Log every command and alert in backend.

Done when:

- system can detect, alert, and actuate end-to-end

## Phase 6: Edge Optimization

Objective:

Decide whether part of inference should run on the ESP32-S3.

Tasks:

1. Benchmark server-side latency.
2. Evaluate TinyML conversion only if needed.
3. Keep safety-critical fallback rules on-device.
4. Use local rules if network fails.

Recommendation:

Do not start with TinyML. First make the server-side system correct, observable, and well-labeled.

## Immediate Priority Order

1. Clean the repo and document dependencies.
2. Build backend ingestion and storage.
3. Stream one real ESP32 device into the backend.
4. Rewire dashboard to backend data.
5. Add zone-aware digital twin view.
6. Start collecting real labeled data.
7. Retrain and evaluate ML.
8. Add buzzer, relay, and SMS workflows.

## What You Are Still Left With

### Device/software integration

- ESP32 firmware
- ingestion API or MQTT consumer
- live database storage
- device health monitoring
- command channel back to hardware

### Digital twin

- building and zone model
- device placement
- zone status engine
- incident map
- alert replay and history

### ML

- real data collection
- labeling workflow
- feature engineering from time windows
- model comparison
- reproducible training and evaluation
- live inference service

### Supporting engineering work

- documentation
- dependency management
- testing
- deployment setup
- logging and observability
- security and access control if multiple users are involved

## Suggested First Coding Sprint

If we start building now, the first sprint should be:

1. Add `requirements.txt`.
2. Create a small FastAPI backend with `/telemetry` ingestion.
3. Save readings to SQLite or PostgreSQL.
4. Expose `/telemetry/latest` and `/zones/status`.
5. Update the dashboard to read from the backend.

This gives the project its first real software backbone.

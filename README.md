# Smart IoT-Based Multi-Sensor Fire Detection System with Digital Twin Integration

This project is a smart fire detection system that combines IoT sensing, multi-sensor data fusion, machine learning-based classification, and a digital twin dashboard for real-time monitoring.

Instead of relying on only one signal such as smoke, the system combines multiple environmental signals to reduce false alarms and improve fire detection reliability.

## Problem Statement

Traditional fire alarms often trigger false alerts because they react to a single condition such as smoke or heat. In real indoor spaces, that can be caused by:

- cooking smoke
- steam
- temporary humidity changes
- dust and airborne particles
- short-term environmental fluctuations

This project aims to reduce those false positives by using multiple sensors together and classifying the environment into:

- `NORMAL`
- `WARNING`
- `FIRE`

## Project Goal

Build a low-cost, scalable fire detection framework that:

- collects live environmental data with an ESP32
- uses ML to classify fire risk
- shows system state in a digital twin dashboard
- supports emergency alerts and actuator triggering

## System Architecture

The project is designed in four layers.

### 1. IoT Sensor Network

The ESP32-S3 / ESP32 collects data from multiple sensors:

- PMS7003 for smoke / PM2.5
- MQ-7 for carbon monoxide
- 5-channel flame sensor
- DHT22 for temperature and humidity
- PIR for motion detection
- LDR for flame flicker signature

### 2. Intelligent Decision Layer

Sensor values are fused and classified by a machine learning model into:

- `NORMAL`
- `WARNING`
- `FIRE`

The model uses multiple contextual signals instead of fixed threshold logic only.

### 3. Digital Twin Monitoring Layer

A dashboard shows:

- live telemetry
- system status
- time-series plots
- gauge indicators
- detection history

### 4. Emergency Response Layer

When a fire condition is detected, the intended final system should support:

- local buzzer activation
- relay-driven actuators such as a fan or water pump
- GSM-based SMS alerts using SIM800L

## Research Contribution

The key contributions of the project are:

- multi-modal sensor fusion for fire detection
- use of PMS7003 for early-stage smoke sensing
- LDR flicker-based flame validation
- ML-assisted classification instead of pure thresholding
- digital twin integration for monitoring and visualization
- low-cost architecture suitable for practical deployment

## Current Working Software Flow

Right now, the repo supports this working flow:

```text
ESP32 sensors
  -> POST JSON over Wi-Fi
sensor_receiver.py
  -> ML inference
  -> rule-based safety overrides
  -> writes fire_sensor_log.csv
digital_twin_dashboard.py
  -> reads CSV every 2 seconds
Browser
  -> live dashboard
```

This is the current practical setup for live testing.

## Current Development Status

Completed:

- baseline ML model training pipeline
- synthetic fire dataset generation
- live sensor simulation utilities
- digital twin dashboard UI
- Flask-based sensor receiver for ESP32 telemetry
- ESP32 sketch for posting live sensor data to backend

Partially completed:

- live ESP32 integration
- sensor calibration and validation
- dashboard-driven monitoring

Pending:

- PMS7003 hardware integration
- real labeled dataset collection
- production-grade ML retraining on real sensor data
- true zone-aware digital twin
- buzzer / relay / GSM automation flow
- deployment hardening and production backend

## Hardware Components

| Category | Component | Model | Purpose |
|---|---|---|---|
| Core Controller | Microcontroller | ESP32-S3-DevKitC-1 | Main processing and communication |
| Smoke Detection | Laser Particle Sensor | PMS7003 | PM1.0 / PM2.5 / PM10 smoke sensing |
| Gas Detection | CO Sensor | MQ-7 | Detects carbon monoxide |
| Flame Detection | IR Flame Sensor | 5-Channel YG1006 Module | Detects flame radiation |
| Environmental Monitoring | Temperature/Humidity Sensor | DHT22 | Measures heat and humidity |
| Motion Detection | PIR Sensor | HC-SR501 | Occupancy context |
| Optical Signature | LDR Module | LM393 LDR Sensor | Flame flicker feature extraction |
| Emergency Alerts | GSM Module | SIM800L V2 | SMS alerts |
| Local Alert | Active Buzzer | 3.3V-5V Module | Local warning |
| Actuation | Relay Module | 5V 30A 1-Channel | External control |
| Power Management | Buck Converter | LM2596 | Stable power for GSM |
| Power Supply | Adapter | 5V 3A DC Adapter | Main supply |

## Repository Structure

```text
.
|-- README.md
|-- requirements.txt
|-- ARCHITECTURE.md
|-- SOFTWARE_ROADMAP.md
|-- backend/
|   |-- README.md
|   `-- app/
|-- firmware/
|   `-- esp32/
|       `-- esp32_fire_detection.ino
`-- ML IOT/
    |-- fire_sensor_data.csv
    `-- Code part/
        |-- fire_ml_model.py
        |-- fire_data_generator.py
        |-- live_data_simulator.py
        |-- smart_fire_logger.py
        |-- sensor_receiver.py
        |-- digital_twin_dashboard.py
        |-- fire_detection_model.pkl
        |-- fire_sensor_log.csv
        `-- building_3d_model.json
```

## Important Files

- `ML IOT/Code part/fire_ml_model.py`
  Trains and evaluates the baseline fire detection model.

- `ML IOT/Code part/fire_data_generator.py`
  Generates a synthetic labeled dataset for model training.

- `ML IOT/Code part/sensor_receiver.py`
  Receives ESP32 JSON telemetry, runs ML inference, applies rule overrides, and logs to CSV.

- `ML IOT/Code part/digital_twin_dashboard.py`
  Dash dashboard for live monitoring.

- `firmware/esp32/esp32_fire_detection.ino`
  ESP32 firmware for sensor reading and POSTing telemetry to Flask.

- `ARCHITECTURE.md`
  High-level target architecture for the full system.

- `SOFTWARE_ROADMAP.md`
  Implementation roadmap from proof-of-concept to full system.

## Installation

Install Python dependencies from the repo root:

```powershell
cd "c:\Users\vibhu\Downloads\IOT-ML-Project-main\IOT-ML-Project-main"
pip install -r requirements.txt
```

Arduino libraries needed for the ESP32 sketch:

- `DHT sensor library`
- `ArduinoJson`

## How To Run The Project

### 1. Start the Flask receiver

```powershell
cd "c:\Users\vibhu\Downloads\IOT-ML-Project-main\IOT-ML-Project-main\ML IOT\Code part"
python sensor_receiver.py
```

Expected health URL:

- `http://127.0.0.1:5000/health`

### 2. Start the dashboard

Open a second terminal:

```powershell
cd "c:\Users\vibhu\Downloads\IOT-ML-Project-main\IOT-ML-Project-main\ML IOT\Code part"
python digital_twin_dashboard.py
```

Dashboard URL:

- `http://127.0.0.1:8050`

### 3. Configure and flash the ESP32

Open:

- `firmware/esp32/esp32_fire_detection.ino`

Update these values before uploading:

```cpp
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* BACKEND_URL = "http://YOUR_LAPTOP_IP:5000/telemetry";
```

To find your laptop IP on Windows:

```powershell
ipconfig
```

If you are using Windows mobile hotspot, it is often `192.xxx.xxx.x`, but always verify it.

### 4. Open Serial Monitor

The ESP32 should print:

- live sensor values
- Wi-Fi status
- HTTP response code
- backend response

## Example Startup Order

```powershell
# Terminal 1
cd "c:\Users\vibhu\Downloads\IOT-ML-Project-main\IOT-ML-Project-main\ML IOT\Code part"
python sensor_receiver.py

# Terminal 2
cd "c:\Users\vibhu\Downloads\IOT-ML-Project-main\IOT-ML-Project-main\ML IOT\Code part"
python digital_twin_dashboard.py
```

Then:

1. upload `esp32_fire_detection.ino`
2. open Serial Monitor
3. open `http://127.0.0.1:8050`

## ML Pipeline

The current ML flow is:

1. generate training data with `fire_data_generator.py`
2. train the classifier with `fire_ml_model.py`
3. save the trained model as `fire_detection_model.pkl`
4. run live inference in `sensor_receiver.py`
5. apply rule-based safety overrides
6. log results to `fire_sensor_log.csv`
7. display them in the dashboard

### Current ML Inputs

The model expects these features:

- `Temperature`
- `Humidity`
- `Smoke_ADC`
- `CO_ADC`
- `Flame`
- `LDR_ADC`
- `LDR_Flicker`
- `Motion`

### Current Hardware Note

PMS7003 is not yet wired into the live ESP32 path, so `sensor_receiver.py` currently uses a temporary CO-based smoke proxy for `Smoke_ADC`.

This should be replaced with real PM values once PMS7003 is integrated.

## ESP32 Telemetry Payload

The ESP32 currently sends JSON in this shape:

```json
{
  "device_id": "esp32_001",
  "timestamp": "2026-04-16T11:19:34Z",
  "temperature": 28.0,
  "humidity": 54.0,
  "co_adc": 883,
  "ldr_adc": 2954,
  "ldr_flicker": 2.3,
  "flame": 1,
  "motion": 0,
  "mq7_warmed": true
}
```

## Known Issues And Notes

- The flame sensor may need logic inversion or threshold tuning depending on your module.
- MQ-7 readings are unreliable before warm-up is complete.
- PMS7003 live integration is still pending.
- The current dashboard is a CSV-driven digital twin demo, not a full zone-aware production twin yet.
- The FastAPI backend scaffold exists in `backend/`, but the active live workflow currently uses Flask + CSV because it matches the present ESP32-to-dashboard testing setup.

## Troubleshooting

### ESP32 shows HTTP response `-1`

Check:

- `sensor_receiver.py` is running
- `BACKEND_URL` uses your laptop IP, not `127.0.0.1`
- laptop and ESP32 are on the same Wi-Fi/hotspot
- Windows firewall allows Python / port `5000`

### Browser cannot open `127.0.0.1:5000/health`

That means `sensor_receiver.py` is not running, or it crashed.

### Dashboard shows no data

Check:

- `sensor_receiver.py` is receiving POSTs
- `fire_sensor_log.csv` is being updated
- `digital_twin_dashboard.py` is running

### Flame is always detected

Likely causes:

- flame logic inversion
- flame module threshold potentiometer needs tuning
- noisy or incorrect wiring

## Roadmap

The bigger software goals are documented in:

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [SOFTWARE_ROADMAP.md](./SOFTWARE_ROADMAP.md)

The next major steps are:

1. integrate PMS7003 into live ESP32 telemetry
2. calibrate sensors and collect real labeled data
3. retrain the model on real data
4. improve the digital twin into a real zone-aware system
5. connect buzzer, relay, and SIM800L for full emergency response

## Final Objective

The final objective of this project is to deliver a practical, scalable, and intelligent indoor fire detection system that improves safety through:

- real-time sensing
- ML-based decision-making
- digital twin monitoring
- automated emergency response

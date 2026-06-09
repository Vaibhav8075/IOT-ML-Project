# Smart IoT-Based Multi-Sensor Fire Detection System with Digital Twin Integration

This project is a smart fire detection system that combines IoT sensing, multi-sensor data fusion, machine learning-based classification, and a digital twin dashboard for real-time monitoring.

Instead of relying on only one signal such as smoke, the system combines multiple environmental signals to reduce false alarms and improve fire detection reliability.

---

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

---

## Project Goal

Build a low-cost, scalable fire detection framework that:

- collects live environmental data with an ESP32-S3
- uses ML to classify fire risk
- shows system state in a digital twin dashboard
- supports emergency alerts and actuator triggering

---

## Hardware — ESP32-S3 N8R8

This project runs on the **ESP32-S3-WROOM-1 N8R8** (8MB Flash, 8MB PSRAM).

> **Important:** This board uses a **CP210x USB-to-UART bridge**, not USB CDC. Serial output works through the CP210x chip directly. USB CDC on Boot must be **Disabled** in Arduino IDE.

### Arduino IDE Board Settings

| Setting | Value |
|---|---|
| Board | ESP32S3 Dev Module |
| Port | COM10 (or whichever shows as Silicon Labs CP210x) |
| USB CDC on Boot | **Disabled** |
| Upload Mode | **UART0** |
| Upload Speed | 921600 |
| Flash Size | 8MB (64Mb) |
| PSRAM | OPI PSRAM |

### Pin Definitions

| Sensor | GPIO Pin |
|---|---|
| PIR (HC-SR501) | GPIO 15 |
| LDR Module | GPIO 4 |
| MQ-7 (CO sensor) | GPIO 5 |
| Flame Sensor (D1 digital) | GPIO 16 |
| DHT22 (data) | GPIO 14 |

> These pins use ADC1 only (GPIO 1–10 range for analog). ADC2 pins conflict with WiFi on ESP32-S3 and must not be used for analog sensors.

### Wiring Notes

- DHT22 requires a **10kΩ pull-up resistor** between DATA and 3.3V
- PIR and MQ-7 are powered from **5V** but their signal pins are 3.3V compatible
- Flame sensor is **active LOW** — reads LOW when flame detected

---

## System Architecture

The project is designed in four layers.

### 1. IoT Sensor Network

The ESP32-S3 collects data from multiple sensors:

- MQ-7 for carbon monoxide
- DHT22 for temperature and humidity
- 5-channel flame sensor
- PIR for motion detection
- LDR for flame flicker signature

### 2. Intelligent Decision Layer

Sensor values are fused and classified by a machine learning model into `NORMAL`, `WARNING`, or `FIRE`. The model uses multiple contextual signals and includes rule-based safety overrides on top of the ML prediction.

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

---

## ML Model

### Algorithm

Random Forest Classifier

### Training Configuration

```python
RandomForestClassifier(
    n_estimators=300,
    min_samples_leaf=2,
    class_weight='balanced',
    random_state=42
)
```

### Dataset

`fire_detection_model.pkl` was trained on a combined dataset of **367,550 rows** from real indoor fire detection experiments (not synthetic data). Sources used:

- Indoor Fire Dataset with Distributed Multi-Sensor Nodes
- Smoke Detection IoT CSV

### Model Performance

| Metric | Value |
|---|---|
| Test Accuracy | 94.93% |
| Fire Recall | 98% |
| No-Fire Precision | 99% |

### Feature Importances

| Feature | Importance |
|---|---|
| PM2.5 / Smoke proxy | 46.6% |
| H2 / CO proxy | 26.6% |
| CO ADC | 13.8% |
| Temperature | 6.8% |
| Humidity | 6.2% |

### Important Note on Real-World Accuracy

The model was trained on lab-collected data, not on readings from your specific sensors. Real-world accuracy will depend on sensor calibration and environmental conditions. Once live data is collected from the actual hardware, retraining with real labeled readings will significantly improve deployment reliability.

### Files

| File | Purpose |
|---|---|
| `fire_detection_model.pkl` | Trained RandomForest classifier |
| `fire_scaler.pkl` | StandardScaler — must be loaded alongside the model |

Both files must be in the same folder as `sensor_receiver.py`.

---

## Current Working Software Flow

```text
ESP32-S3 sensors
  -> POST JSON over Wi-Fi every 2 seconds
sensor_receiver.py
  -> ML inference (RandomForest)
  -> rule-based safety overrides
  -> writes fire_sensor_log.csv
digital_twin_dashboard.py
  -> reads CSV every 2 seconds
Browser
  -> live dashboard at http://127.0.0.1:8050
```

---

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
|       |-- main.py
|       |-- db.py
|       `-- schemas.py
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
        |-- fire_scaler.pkl
        |-- fire_sensor_log.csv
        `-- building_3d_model.json
```

---

## Installation

### Python Dependencies

Run once from the project root:

```powershell
cd "IOT-ML-Project-main"
pip install -r requirements.txt
```

Or install directly:

```powershell
pip install flask scikit-learn joblib pandas numpy dash plotly
```

### Arduino Libraries

Install these in Arduino IDE via Sketch → Include Library → Manage Libraries:

- `DHT sensor library` by Adafruit
- `Adafruit Unified Sensor` (installed automatically with DHT)
- `ArduinoJson` by Benoit Blanchon

---

## How To Run The Project

### Step 1 — Find your laptop IP

Run this every time before starting, because your IP can change:

```powershell
ipconfig
```

Look for **IPv4 Address** under your Wi-Fi adapter (e.g. `192.168.x.x`).

Update this line in `esp32_fire_detection.ino` if it changed:

```cpp
const char* BACKEND_URL = "http://YOUR_LAPTOP_IP:5000/telemetry";
```

### Step 2 — Start the Flask receiver

Open a terminal:

```powershell
cd "IOT-ML-Project-main\ML IOT\Code part"
python sensor_receiver.py
```

Verify it is running by opening in your browser:

```
http://127.0.0.1:5000/health
```

### Step 3 — Start the dashboard

Open a second terminal:

```powershell
cd "IOT-ML-Project-main\ML IOT\Code part"
python digital_twin_dashboard.py
```

Dashboard URL:

```
http://127.0.0.1:8050
```

### Step 4 — Upload firmware to ESP32-S3

Open `firmware/esp32/esp32_fire_detection.ino` in Arduino IDE.

Update WiFi credentials and backend URL:

```cpp
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* BACKEND_URL   = "http://YOUR_LAPTOP_IP:5000/telemetry";
```

Set Tools menu settings (see Hardware section above), then click Upload.

### Step 5 — Open Serial Monitor

After upload completes:

1. Open Serial Monitor (Ctrl+Shift+M)
2. Set baud rate to `115200`
3. Press the **EN/RESET** button on the board

Expected output:

```
=== BOOT OK ===
Connecting to WiFi......
WiFi connected
IP: 192.168.x.x
Syncing NTP....
NTP synced
MQ-7 warming up (90 sec)...
System ready

--------------------------------------------
[DHT22]  Temp     : 28.5 C
[DHT22]  Humidity : 54.0 %
[MQ-7]   CO ADC   : 420  (warming up - 87s left)
[LDR]    ADC      : 2954
[LDR]    Flicker  : 2.3
[PIR]    Motion   : no
[FLAME]  D1       : none
[HTTP]   Response : 200
[ML]     Result   : {"status":"ok","ml_pred":0,"final_label":"NORMAL","reason":"ML"}
```

---

## Example Full Startup (Copy-Paste)

```powershell
# Terminal 1 — backend
cd "IOT-ML-Project-main\ML IOT\Code part"
python sensor_receiver.py

# Terminal 2 — dashboard
cd "IOT-ML-Project-main\ML IOT\Code part"
python digital_twin_dashboard.py
```

Then upload firmware, open Serial Monitor, open `http://127.0.0.1:8050`.

---

## ESP32 Telemetry Payload

The ESP32-S3 sends JSON in this shape every 2 seconds:

```json
{
  "device_id": "esp32_001",
  "zone_id": "lab_zone",
  "timestamp": "2026-06-08T10:30:00Z",
  "temperature": 28.5,
  "humidity": 54.0,
  "co_adc": 420,
  "ldr_adc": 2954,
  "ldr_flicker": 2.3,
  "flame": 0,
  "motion": 0,
  "mq7_warmed": false
}
```

---

## Troubleshooting

### Serial Monitor is blank

- Check Tools → USB CDC on Boot → **Disabled** (critical for CP210x boards)
- Check Tools → Upload Mode → **UART0**
- After upload, close and reopen Serial Monitor, then press EN/RESET
- Verify COM10 is the Silicon Labs CP210x port in Device Manager

### ESP32 shows HTTP response `-1`

- Confirm `sensor_receiver.py` is running
- Confirm `BACKEND_URL` uses your laptop IPv4 — not `127.0.0.1`
- Confirm laptop and ESP32 are on the same Wi-Fi hotspot
- Allow Python through Windows Firewall, or run: `netsh advfirewall firewall add rule name="Flask5000" dir=in action=allow protocol=TCP localport=5000`

### DHT22 returns NAN

- Missing 10kΩ pull-up resistor between DATA and 3.3V
- Wrong pin — confirm data wire is on GPIO 14
- Reading interval too short — minimum 2 seconds between reads

### Dashboard shows no data

- Confirm `sensor_receiver.py` is receiving POSTs (watch terminal output)
- Confirm `fire_sensor_log.csv` file is being updated
- Confirm `digital_twin_dashboard.py` is running in a separate terminal

### Flame is always detected

- Flame sensor is active LOW — adjust potentiometer on the module
- Check wiring — D0 (digital out) goes to GPIO 16

### MQ-7 readings are very high or erratic

- MQ-7 requires 90 seconds warm-up — readings before that are unreliable
- The sketch shows a countdown: `(warming up - Xs left)`
- Use a stable 5V supply — voltage drop causes erratic ADC values

---

## Current Development Status

Completed:

- ESP32-S3 N8R8 firmware with correct S3 pin mapping
- ML model trained on 367k real fire detection dataset rows
- Flask-based sensor receiver with ML inference and rule overrides
- Digital twin dashboard
- CSV logging of all readings and predictions

Partially completed:

- Live ESP32-S3 hardware integration and sensor validation
- Dashboard-driven monitoring

Pending:

- PMS7003 smoke sensor hardware integration
- Real labeled dataset collection from live sensors
- ML retraining on real sensor readings
- True zone-aware digital twin
- Buzzer, relay, and SIM800L emergency response automation
- Production backend (FastAPI scaffold exists in `backend/`)

---

## Hardware Components

| Category | Component | Model | Purpose |
|---|---|---|---|
| Core Controller | Microcontroller | ESP32-S3-WROOM-1 N8R8 | Main processing and WiFi |
| Gas Detection | CO Sensor | MQ-7 | Carbon monoxide detection |
| Flame Detection | IR Flame Sensor | 5-Channel YG1006 | Flame radiation detection |
| Environmental | Temp/Humidity | DHT22 | Temperature and humidity |
| Motion Detection | PIR Sensor | HC-SR501 | Occupancy context |
| Optical Signature | LDR Module | LM393 | Flame flicker extraction |
| Emergency Alerts | GSM Module | SIM800L V2 | SMS alerts (pending) |
| Local Alert | Active Buzzer | 3.3V-5V | Local warning (pending) |
| Actuation | Relay Module | 5V 30A 1-Channel | External control (pending) |
| Power | Adapter | 5V 3A DC | Main supply |

---

## Roadmap

Next major steps:

1. Confirm live ESP32-S3 serial output and sensor readings
2. Confirm backend receiving JSON and ML predicting correctly
3. Collect real readings from live sensors across normal and fire conditions
4. Retrain model on real labeled data
5. Integrate PMS7003 smoke sensor into firmware
6. Connect buzzer and relay for automated emergency response
7. Integrate SIM800L for SMS alerts

Full roadmap: [SOFTWARE_ROADMAP.md](./SOFTWARE_ROADMAP.md)  
Architecture details: [ARCHITECTURE.md](./ARCHITECTURE.md)

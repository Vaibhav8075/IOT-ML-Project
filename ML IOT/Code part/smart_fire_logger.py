# smart_fire_logger.py
# Simulates ESP32 sensor readings at ADC scale, runs ML inference,
# applies rule-based overrides, and logs everything to fire_sensor_log.csv.
# Labels: 0 = NORMAL   1 = WARNING   2 = FIRE

import csv
import time
import random
from datetime import datetime
import joblib
import os

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE   = os.path.join(BASE_DIR, "fire_detection_model.pkl")
LOG_CSV      = os.path.join(BASE_DIR, "fire_sensor_log.csv")
POLL_SECONDS = 2.0

FEATURES = [
    "Temperature", "Humidity", "Smoke_ADC", "CO_ADC",
    "Flame", "LDR_ADC", "LDR_Flicker", "Motion"
]

LABEL_TEXT = {0: "NORMAL", 1: "WARNING", 2: "FIRE"}

# ── Load model ────────────────────────────────────────────────────────────────

if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(f"{MODEL_FILE} not found. Run fire_ml_model.py first.")

model = joblib.load(MODEL_FILE)
print(f"Model loaded from {MODEL_FILE}")

# ── CSV header ────────────────────────────────────────────────────────────────

if not os.path.exists(LOG_CSV) or os.path.getsize(LOG_CSV) == 0:
    with open(LOG_CSV, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            "Timestamp", "Scenario",
            "Temperature", "Humidity", "Smoke_ADC", "CO_ADC",
            "Flame", "LDR_ADC", "LDR_Flicker", "Motion",
            "ML_Pred", "Final_Label", "Reason"
        ])

# ── Scenario simulators (ADC-scale, matching fire_data_generator.py) ─────────

def _ldr(flame):
    return round(random.uniform(50, 350), 0) if flame else round(random.uniform(900, 3600), 0)

def _flicker(flame):
    return round(random.uniform(250, 850), 1) if flame else round(random.uniform(0, 60), 1)

def sim_normal():
    f = 0
    return ("normal",
            round(random.uniform(18, 30), 2),
            round(random.uniform(35, 65), 2),
            round(random.uniform(0, 300), 0),
            round(random.uniform(0, 400), 0),
            f, _ldr(f), _flicker(f),
            random.choice([0, 1]))

def sim_cooking():
    f = 0
    return ("cooking",
            round(random.uniform(28, 65), 2),
            round(random.uniform(55, 90), 2),
            round(random.uniform(600, 2200), 0),
            round(random.uniform(0, 500), 0),
            f, _ldr(f), _flicker(f),
            1)

def sim_electrical():
    f = random.choices([0, 1], weights=[85, 15])[0]
    return ("electrical",
            round(random.uniform(40, 90), 2),
            round(random.uniform(20, 55), 2),
            round(random.uniform(800, 2500), 0),
            round(random.uniform(800, 2000), 0),
            f, _ldr(f), _flicker(f),
            random.choice([0, 1]))

def sim_smoldering():
    f = random.choices([0, 1], weights=[70, 30])[0]
    return ("smoldering",
            round(random.uniform(50, 110), 2),
            round(random.uniform(10, 45), 2),
            round(random.uniform(1500, 3500), 0),
            round(random.uniform(1500, 3000), 0),
            f, _ldr(f), _flicker(f),
            random.choice([0, 1]))

def sim_open_flame():
    f = 1
    return ("open_flame",
            round(random.uniform(90, 200), 2),
            round(random.uniform(5, 35), 2),
            round(random.uniform(2800, 4095), 0),
            round(random.uniform(2500, 4095), 0),
            f, _ldr(f), _flicker(f),
            random.choice([0, 1]))

SIMULATORS = [sim_normal, sim_cooking, sim_electrical, sim_smoldering, sim_open_flame]
WEIGHTS    = [0.65, 0.18, 0.08, 0.06, 0.03]

# ── Rule-based override ───────────────────────────────────────────────────────
# Applied AFTER ML prediction to catch clear-cut cases and suppress false alarms.

def rule_override(temp, hum, smoke_adc, co_adc, flame, ldr_flicker):
    """
    Returns (override_label, reason) or (None, None) to defer to ML.
    ADC scale: 0–4095.  CO_ADC ~800+ = elevated,  ~2500+ = dangerous.
    """
    # Confirmed open fire — all strong indicators simultaneously
    if flame == 1 and temp > 80 and smoke_adc > 2500 and co_adc > 2000:
        return 2, "Rule: confirmed fire - flame + temp + smoke + CO"

    # Flicker signature + flame → fire
    if flame == 1 and ldr_flicker > 400:
        return 2, "Rule: flame + LDR flicker pattern"

    # Cooking suppression: high smoke + high humidity + low CO + no flame
    if smoke_adc > 600 and hum > 55 and co_adc < 500 and flame == 0 and temp < 70:
        return 0, "Cooking heuristic - suppressed"

    # Smoldering: CO climbing without visible flame
    if co_adc > 1500 and smoke_adc > 1200 and flame == 0 and temp > 45:
        return 1, "Rule: smoldering - CO + smoke, no flame yet"

    return None, None

# ── Main loop ─────────────────────────────────────────────────────────────────

print(f"smart_fire_logger started — logging to {LOG_CSV}")
print("Press Ctrl-C to stop.\n")

try:
    while True:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sim_fn = random.choices(SIMULATORS, weights=WEIGHTS, k=1)[0]
        scenario, temp, hum, smoke_adc, co_adc, flame, ldr_adc, ldr_flicker, motion = sim_fn()

        X = [[temp, hum, smoke_adc, co_adc, flame, ldr_adc, ldr_flicker, motion]]
        ml_pred = int(model.predict(X)[0])

        override, reason = rule_override(temp, hum, smoke_adc, co_adc, flame, ldr_flicker)

        if override is not None:
            final_label = override
            final_reason = reason
        else:
            # ML flagged FIRE but context looks like cooking → downgrade
            if ml_pred == 2 and hum > 65 and flame == 0 and co_adc < 600:
                final_label = 1
                final_reason = "ML=FIRE but humidity/no-flame suggests cooking - downgraded"
            else:
                final_label = ml_pred
                final_reason = "ML"

        label_str = LABEL_TEXT[final_label]

        with open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                ts, scenario,
                temp, hum, smoke_adc, co_adc,
                flame, ldr_adc, ldr_flicker, motion,
                ml_pred, label_str, final_reason
            ])

        alert = " *** ALERT ***" if final_label == 2 else ""
        print(
            f"{ts} | {scenario:<12} | "
            f"T:{temp:6.1f}°C  H:{hum:4.0f}%  "
            f"Smoke:{smoke_adc:5.0f}  CO:{co_adc:5.0f}  "
            f"Flame:{flame}  Flicker:{ldr_flicker:5.1f} | "
            f"ML:{LABEL_TEXT[ml_pred]:<8} → {label_str}{alert}"
        )

        time.sleep(POLL_SECONDS)

except KeyboardInterrupt:
    print("\nLogger stopped.")

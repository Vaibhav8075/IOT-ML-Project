from flask import Flask, request, jsonify
import csv
import os
from datetime import datetime

import joblib


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(BASE_DIR, "fire_detection_model.pkl")
LOG_CSV = os.path.join(BASE_DIR, "fire_sensor_log.csv")

FEATURES = [
    "Temperature",
    "Humidity",
    "Smoke_ADC",
    "CO_ADC",
    "Flame",
    "LDR_ADC",
    "LDR_Flicker",
    "Motion",
]

LABEL_TEXT = {0: "NORMAL", 1: "WARNING", 2: "FIRE"}


if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(f"{MODEL_FILE} not found. Run fire_ml_model.py first.")

model = joblib.load(MODEL_FILE)
print(f"Model loaded from {MODEL_FILE}")


def ensure_log_file():
    if not os.path.exists(LOG_CSV):
        with open(LOG_CSV, "w", newline="", encoding="utf-8") as file_obj:
            csv.writer(file_obj).writerow(
                [
                    "Timestamp",
                    "Source",
                    "Temperature",
                    "Humidity",
                    "Smoke_ADC",
                    "CO_ADC",
                    "Flame",
                    "LDR_ADC",
                    "LDR_Flicker",
                    "Motion",
                    "ML_Pred",
                    "Final_Label",
                    "Reason",
                ]
            )


def rule_override(temp, hum, smoke_adc, co_adc, flame, ldr_flicker):
    if flame == 1 and temp > 80 and smoke_adc > 2500 and co_adc > 2000:
        return 2, "Rule: confirmed fire - flame + temp + smoke + CO"
    if flame == 1 and ldr_flicker > 400:
        return 2, "Rule: flame + LDR flicker pattern"
    if smoke_adc > 600 and hum > 55 and co_adc < 500 and flame == 0 and temp < 70:
        return 0, "Cooking heuristic - suppressed"
    if co_adc > 1500 and smoke_adc > 1200 and flame == 0 and temp > 45:
        return 1, "Rule: smoldering - CO + smoke, no flame yet"
    return None, None


app = Flask(__name__)


@app.route("/telemetry", methods=["POST"])
def telemetry():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "no JSON received"}), 400

    try:
        temp = float(data.get("temperature", 25.0))
        hum = float(data.get("humidity", 50.0))
        co_adc = float(data.get("co_adc", 0.0))
        ldr_adc = float(data.get("ldr_adc", 2000.0))
        ldr_flicker = float(data.get("ldr_flicker", 0.0))
        flame = int(data.get("flame", 0))
        motion = int(data.get("motion", 0))
        mq7_warmed = bool(data.get("mq7_warmed", True))
        device_id = str(data.get("device_id", "unknown"))
        _ = data.get("timestamp", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
    except Exception as exc:
        return jsonify({"error": f"field parse error: {exc}"}), 400

    if not mq7_warmed:
        co_adc_for_ml = 0.0
    else:
        co_adc_for_ml = co_adc

    # PMS7003 is not wired yet, so use a temporary smoke proxy from CO.
    smoke_adc_proxy = min(co_adc_for_ml * 1.3, 4095.0)

    features = [[
        temp,
        hum,
        smoke_adc_proxy,
        co_adc_for_ml,
        flame,
        ldr_adc,
        ldr_flicker,
        motion,
    ]]
    ml_pred = int(model.predict(features)[0])

    override, reason = rule_override(
        temp, hum, smoke_adc_proxy, co_adc_for_ml, flame, ldr_flicker
    )

    if override is not None:
        final_label = override
        final_reason = reason
    elif ml_pred == 2 and hum > 65 and flame == 0 and co_adc_for_ml < 600:
        final_label = 1
        final_reason = "ML=FIRE but high humidity + no flame - downgraded"
    else:
        final_label = ml_pred
        final_reason = "ML"

    label_str = LABEL_TEXT[final_label]
    log_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_CSV, "a", newline="", encoding="utf-8") as file_obj:
        csv.writer(file_obj).writerow(
            [
                log_ts,
                device_id,
                round(temp, 1),
                round(hum, 1),
                round(smoke_adc_proxy, 0),
                round(co_adc_for_ml, 0),
                flame,
                round(ldr_adc, 0),
                round(ldr_flicker, 1),
                motion,
                ml_pred,
                label_str,
                final_reason,
            ]
        )

    alert = "  *** ALERT ***" if final_label == 2 else ""
    print(
        f"{log_ts} | {device_id} | "
        f"T:{temp:.1f}C  H:{hum:.0f}%  "
        f"CO:{co_adc:.0f}  LDR:{ldr_adc:.0f}  Flicker:{ldr_flicker:.1f}  "
        f"Flame:{flame}  Motion:{motion} | "
        f"ML:{LABEL_TEXT[ml_pred]:<8} -> {label_str}{alert}"
    )

    return jsonify(
        {
            "status": "ok",
            "ml_pred": ml_pred,
            "final_label": label_str,
            "reason": final_reason,
        }
    ), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running", "model": MODEL_FILE}), 200


if __name__ == "__main__":
    ensure_log_file()
    print("sensor_receiver.py started")
    print("Listening on http://0.0.0.0:5000/telemetry")
    print("ESP32 should POST to http://<YOUR_LAPTOP_IP>:5000/telemetry")
    print("Press Ctrl-C to stop.\n")
    app.run(host="0.0.0.0", port=5000, debug=False)

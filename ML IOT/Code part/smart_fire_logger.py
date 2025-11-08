# smart_fire_logger.py
import csv
import time
import random
from datetime import datetime
import joblib
import os

MODEL_FILE = "fire_detection_model.pkl"
LOG_CSV = "fire_sensor_log.csv"
POLL_SECONDS = 2.0

# Load model
if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(f"{MODEL_FILE} not found. Run fire_ml_model.py first.")

model = joblib.load(MODEL_FILE)

# Ensure CSV exists and header present
if not os.path.exists(LOG_CSV):
    with open(LOG_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp","Temperature","Humidity","Smoke","CO","Flame","Pressure","Motion","ML_Pred","Final_Label","Reason"])

def simulate_sensors():
    scenario = random.choices(
        population=["normal","cooking","electrical","smolder","flame"],
        weights=[0.70, 0.15, 0.07, 0.06, 0.02],
        k=1
    )[0]

    if scenario == "normal":
        temp = round(random.uniform(18, 30), 2)
        hum = round(random.uniform(30, 60), 2)
        smoke = round(random.uniform(0, 80), 2)
        co = round(random.uniform(0, 3), 2)
        flame = 0.0
        pressure = round(random.uniform(1008, 1015), 2)
        motion = random.choice([0,1])
    elif scenario == "cooking":
        temp = round(random.uniform(30, 70), 2)
        hum = round(random.uniform(45, 90), 2)
        smoke = round(random.uniform(150, 800), 2)
        co = round(random.uniform(0, 5), 2)
        flame = random.choice([0.0, 0.1])
        pressure = round(random.uniform(1008, 1016), 2)
        motion = 1
    elif scenario == "electrical":
        temp = round(random.uniform(35, 95), 2)
        hum = round(random.uniform(20, 60), 2)
        smoke = round(random.uniform(20, 450), 2)
        co = round(random.uniform(1, 10), 2)
        flame = random.choice([0.0, 0.2])
        pressure = round(random.uniform(1004, 1012), 2)
        motion = random.choice([0,1])
    elif scenario == "smolder":
        temp = round(random.uniform(40, 100), 2)
        hum = round(random.uniform(10, 50), 2)
        smoke = round(random.uniform(300, 900), 2)
        co = round(random.uniform(5, 25), 2)
        flame = random.choice([0.0, 0.3])
        pressure = round(random.uniform(1000, 1010), 2)
        motion = random.choice([0,1])
    else:  # flame
        temp = round(random.uniform(90, 200), 2)
        hum = round(random.uniform(5, 40), 2)
        smoke = round(random.uniform(700, 2000), 2)
        co = round(random.uniform(10, 60), 2)
        flame = 1.0
        pressure = round(random.uniform(990, 1008), 2)
        motion = random.choice([0,1])

    return [temp, hum, smoke, co, flame, pressure, motion, scenario]

def rule_based_override(temp, hum, smoke, co, flame):
    # Cooking heuristic: high smoke + high humidity + low CO + low flame -> suppress
    if smoke > 150 and hum > 50 and co < 5 and flame < 0.2 and temp < 80:
        return 0, "Cooking heuristic -> suppressed"
    # Strong fire heuristic
    if (temp > 80 and smoke > 600) or flame >= 1.0 or (co > 15 and smoke > 500):
        return 2, "Rule: strong fire indicators"
    # Electrical fault heuristic
    if temp > 50 and smoke > 100 and co > 4 and flame < 0.5:
        return 1, "Rule: electrical/elevated risk"
    return None, None

print("✅ smart_fire_logger started. Logging to", LOG_CSV)
while True:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    temp, hum, smoke, co, flame, pressure, motion, scenario = simulate_sensors()

    X = [[temp, hum, smoke, co, flame, pressure, motion]]
    ml_pred = int(model.predict(X)[0])  # 0,1,2

    override_label, reason = rule_based_override(temp, hum, smoke, co, flame)
    final_label = ml_pred
    final_reason = "ML"

    if override_label is not None:
        final_label = override_label
        final_reason = reason
    else:
        # If ML flagged fire but humidity high and low flame and low CO -> likely cooking; downgrade
        if ml_pred == 2 and hum > 70 and flame < 0.2 and co < 6:
            final_label = 1
            final_reason = "ML flagged but humidity suggests cooking -> downgraded"

    label_text = {0:"NORMAL", 1:"WARNING", 2:"FIRE"}[final_label]

    with open(LOG_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([ts, temp, hum, smoke, co, flame, pressure, motion, ml_pred, label_text, final_reason])

    print(f"{ts} | Scen:{scenario:9s} | T:{temp:.1f}C H:{hum:.0f}% S:{smoke:.0f}ppm CO:{co:.1f} Flame:{flame:.2f} ML:{ml_pred} Final:{label_text} ({final_reason})")
    time.sleep(POLL_SECONDS)

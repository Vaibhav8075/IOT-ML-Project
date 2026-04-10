# fire_data_generator.py
# Generates synthetic training data matched to actual ESP32 sensor output scales:
#   Temperature  : °C         (DHT22)
#   Humidity     : %          (DHT22)
#   Smoke        : ADC 0-4095 (PMS7003 proxy via analog, or normalised PM2.5)
#   CO           : ADC 0-4095 (MQ-7 raw ADC on GPIO 35)
#   Flame        : 0 or 1     (5-channel IR module, digital)
#   LDR          : ADC 0-4095 (LM393 AO on GPIO 34 — lower = brighter)
#   Motion       : 0 or 1     (HC-SR501 digital)
#   Label        : 0=Normal  1=Warning  2=Fire

import csv
import random

OUTFILE    = "fire_sensor_data.csv"
N_PER_CLASS = 1500   # 1500 × 5 scenarios = 7500 rows total

# ── helpers ──────────────────────────────────────────────────────────────────

def ldr_for_flame(flame_present):
    """LDR reads LOW (bright) when flame IR/light is present."""
    if flame_present:
        return round(random.uniform(50, 400), 0)   # very bright
    return round(random.uniform(800, 3800), 0)      # normal ambient

def ldr_flicker(flame_present):
    """
    Flicker feature: standard deviation of rapid LDR samples.
    Real implementation samples LDR ~10x over 500ms on ESP32.
    Here we simulate a single representative value.
    """
    if flame_present:
        return round(random.uniform(200, 900), 1)   # high variance = flicker
    return round(random.uniform(0, 80), 1)          # stable ambient

# ── scenario generators ───────────────────────────────────────────────────────

def gen_normal():
    flame = 0
    return {
        "Temperature"  : round(random.uniform(18, 30), 2),
        "Humidity"     : round(random.uniform(35, 65), 2),
        "Smoke_ADC"    : round(random.uniform(0, 300), 0),
        "CO_ADC"       : round(random.uniform(0, 400), 0),
        "Flame"        : flame,
        "LDR_ADC"      : ldr_for_flame(False),
        "LDR_Flicker"  : ldr_flicker(False),
        "Motion"       : random.choice([0, 1]),
        "Label"        : 0
    }

def gen_cooking():
    """High smoke + high humidity + low CO + no flame + person present → NOT fire."""
    flame = 0
    return {
        "Temperature"  : round(random.uniform(28, 65), 2),
        "Humidity"     : round(random.uniform(55, 90), 2),
        "Smoke_ADC"    : round(random.uniform(600, 2200), 0),
        "CO_ADC"       : round(random.uniform(0, 500), 0),
        "Flame"        : flame,
        "LDR_ADC"      : ldr_for_flame(False),
        "LDR_Flicker"  : ldr_flicker(False),
        "Motion"       : 1,   # someone is cooking
        "Label"        : 0
    }

def gen_electrical_fault():
    """Smoldering wire: rising temp + moderate smoke + CO spike + no open flame."""
    flame = random.choices([0, 1], weights=[85, 15])[0]
    return {
        "Temperature"  : round(random.uniform(40, 90), 2),
        "Humidity"     : round(random.uniform(20, 55), 2),
        "Smoke_ADC"    : round(random.uniform(800, 2500), 0),
        "CO_ADC"       : round(random.uniform(800, 2000), 0),
        "Flame"        : flame,
        "LDR_ADC"      : ldr_for_flame(bool(flame)),
        "LDR_Flicker"  : ldr_flicker(bool(flame)),
        "Motion"       : random.choice([0, 1]),
        "Label"        : 1
    }

def gen_smoldering():
    """Early fire: no visible flame yet, CO rising fast, temp climbing."""
    flame = random.choices([0, 1], weights=[70, 30])[0]
    return {
        "Temperature"  : round(random.uniform(50, 110), 2),
        "Humidity"     : round(random.uniform(10, 45), 2),
        "Smoke_ADC"    : round(random.uniform(1500, 3500), 0),
        "CO_ADC"       : round(random.uniform(1500, 3000), 0),
        "Flame"        : flame,
        "LDR_ADC"      : ldr_for_flame(bool(flame)),
        "LDR_Flicker"  : ldr_flicker(bool(flame)),
        "Motion"       : random.choice([0, 1]),
        "Label"        : 1
    }

def gen_open_flame():
    """Active fire: flame confirmed, extreme temp, maxed smoke and CO."""
    flame = 1
    return {
        "Temperature"  : round(random.uniform(90, 200), 2),
        "Humidity"     : round(random.uniform(5, 35), 2),
        "Smoke_ADC"    : round(random.uniform(2800, 4095), 0),
        "CO_ADC"       : round(random.uniform(2500, 4095), 0),
        "Flame"        : flame,
        "LDR_ADC"      : ldr_for_flame(True),
        "LDR_Flicker"  : ldr_flicker(True),
        "Motion"       : random.choice([0, 1]),
        "Label"        : 2
    }

# ── main ─────────────────────────────────────────────────────────────────────

def main():
    generators = [gen_normal, gen_cooking, gen_electrical_fault, gen_smoldering, gen_open_flame]
    rows = []
    for _ in range(N_PER_CLASS):
        for g in generators:
            rows.append(g())

    random.shuffle(rows)

    header = ["Temperature", "Humidity", "Smoke_ADC", "CO_ADC",
              "Flame", "LDR_ADC", "LDR_Flicker", "Motion", "Label"]

    with open(OUTFILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    label_counts = {0: 0, 1: 0, 2: 0}
    for r in rows:
        label_counts[r["Label"]] += 1

    print(f"Wrote {len(rows)} rows to {OUTFILE}")
    print(f"  Label 0 (Normal)  : {label_counts[0]}")
    print(f"  Label 1 (Warning) : {label_counts[1]}")
    print(f"  Label 2 (Fire)    : {label_counts[2]}")

if __name__ == "__main__":
    main()
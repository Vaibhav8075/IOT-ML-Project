import csv
import os
import random


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTFILE = os.path.join(BASE_DIR, "fire_sensor_data.csv")
N_PER_CLASS = 1500

HEADER = [
    "Temperature",
    "Humidity",
    "Smoke_ADC",
    "CO_ADC",
    "Flame",
    "LDR_ADC",
    "LDR_Flicker",
    "Motion",
    "Label",
]


def ldr_for_flame(flame_present):
    """LDR reads low when bright flame light is present."""
    if flame_present:
        return round(random.uniform(50, 400), 0)
    return round(random.uniform(800, 3800), 0)


def ldr_flicker(flame_present):
    """
    Simulate short-window LDR variation to mimic flame flicker.
    The real device would compute this from rapid consecutive samples.
    """
    if flame_present:
        return round(random.uniform(200, 900), 1)
    return round(random.uniform(0, 80), 1)


def gen_normal():
    flame = 0
    return {
        "Temperature": round(random.uniform(18, 30), 2),
        "Humidity": round(random.uniform(35, 65), 2),
        "Smoke_ADC": round(random.uniform(0, 300), 0),
        "CO_ADC": round(random.uniform(0, 400), 0),
        "Flame": flame,
        "LDR_ADC": ldr_for_flame(False),
        "LDR_Flicker": ldr_flicker(False),
        "Motion": random.choice([0, 1]),
        "Label": 0,
    }


def gen_cooking():
    """High smoke and humidity without strong CO or flame should stay non-fire."""
    flame = 0
    return {
        "Temperature": round(random.uniform(28, 65), 2),
        "Humidity": round(random.uniform(55, 90), 2),
        "Smoke_ADC": round(random.uniform(600, 2200), 0),
        "CO_ADC": round(random.uniform(0, 500), 0),
        "Flame": flame,
        "LDR_ADC": ldr_for_flame(False),
        "LDR_Flicker": ldr_flicker(False),
        "Motion": 1,
        "Label": 0,
    }


def gen_electrical_fault():
    """Smoldering wire: rising temp, moderate smoke, elevated CO, limited flame."""
    flame = random.choices([0, 1], weights=[85, 15])[0]
    return {
        "Temperature": round(random.uniform(40, 90), 2),
        "Humidity": round(random.uniform(20, 55), 2),
        "Smoke_ADC": round(random.uniform(800, 2500), 0),
        "CO_ADC": round(random.uniform(800, 2000), 0),
        "Flame": flame,
        "LDR_ADC": ldr_for_flame(bool(flame)),
        "LDR_Flicker": ldr_flicker(bool(flame)),
        "Motion": random.choice([0, 1]),
        "Label": 1,
    }


def gen_smoldering():
    """Early fire: no obvious flame yet, but CO and smoke rise sharply."""
    flame = random.choices([0, 1], weights=[70, 30])[0]
    return {
        "Temperature": round(random.uniform(50, 110), 2),
        "Humidity": round(random.uniform(10, 45), 2),
        "Smoke_ADC": round(random.uniform(1500, 3500), 0),
        "CO_ADC": round(random.uniform(1500, 3000), 0),
        "Flame": flame,
        "LDR_ADC": ldr_for_flame(bool(flame)),
        "LDR_Flicker": ldr_flicker(bool(flame)),
        "Motion": random.choice([0, 1]),
        "Label": 1,
    }


def gen_open_flame():
    """Active fire: visible flame with extreme smoke and CO."""
    flame = 1
    return {
        "Temperature": round(random.uniform(90, 200), 2),
        "Humidity": round(random.uniform(5, 35), 2),
        "Smoke_ADC": round(random.uniform(2800, 4095), 0),
        "CO_ADC": round(random.uniform(2500, 4095), 0),
        "Flame": flame,
        "LDR_ADC": ldr_for_flame(True),
        "LDR_Flicker": ldr_flicker(True),
        "Motion": random.choice([0, 1]),
        "Label": 2,
    }


def main():
    generators = [
        gen_normal,
        gen_cooking,
        gen_electrical_fault,
        gen_smoldering,
        gen_open_flame,
    ]

    rows = []
    for _ in range(N_PER_CLASS):
        for generator in generators:
            rows.append(generator())

    random.shuffle(rows)

    with open(OUTFILE, "w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)

    label_counts = {0: 0, 1: 0, 2: 0}
    for row in rows:
        label_counts[row["Label"]] += 1

    print(f"Wrote {len(rows)} rows to {OUTFILE}")
    print(f"  Label 0 (Normal)  : {label_counts[0]}")
    print(f"  Label 1 (Warning) : {label_counts[1]}")
    print(f"  Label 2 (Fire)    : {label_counts[2]}")


if __name__ == "__main__":
    main()

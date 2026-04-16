import csv
import os
import random
import time

import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTFILE = os.path.join(BASE_DIR, "fire_sensor_data.csv")
MAX_ROWS = 300
POLL_SECONDS = 2

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


def file_has_expected_header(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        df = pd.read_csv(path, nrows=0, encoding="utf-8")
    except Exception:
        return False
    return list(df.columns) == HEADER


def ldr_for_flame(flame_present):
    if flame_present:
        return round(random.uniform(50, 400), 0)
    return round(random.uniform(800, 3800), 0)


def ldr_flicker(flame_present):
    if flame_present:
        return round(random.uniform(200, 900), 1)
    return round(random.uniform(0, 80), 1)


def generate_row():
    temp = round(random.uniform(18, 200), 2)
    hum = round(random.uniform(5, 90), 2)
    smoke_adc = round(random.uniform(0, 4095), 0)
    co_adc = round(random.uniform(0, 4095), 0)
    flame = random.choice([0, 1])
    motion = random.choice([0, 1])
    ldr_adc = ldr_for_flame(bool(flame))
    flicker = ldr_flicker(bool(flame))

    if flame == 1 and (smoke_adc > 2500 or co_adc > 2000 or temp > 100):
        label = 2
    elif smoke_adc > 1200 or co_adc > 1000 or temp > 60:
        label = 1
    else:
        label = 0

    return [temp, hum, smoke_adc, co_adc, flame, ldr_adc, flicker, motion, label]


def ensure_file():
    if not file_has_expected_header(OUTFILE):
        with open(OUTFILE, "w", newline="", encoding="utf-8") as file_obj:
            csv.writer(file_obj).writerow(HEADER)


def main():
    ensure_file()
    print("Live data simulator started")

    try:
        while True:
            row = generate_row()
            df = pd.read_csv(OUTFILE, encoding="utf-8")
            df.loc[len(df)] = row
            df = df.tail(MAX_ROWS)
            df.to_csv(OUTFILE, index=False, encoding="utf-8")
            print(
                f"Updated: Temp={row[0]} Smoke={row[2]} "
                f"CO={row[3]} Flame={row[4]} Label={row[-1]}"
            )
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print("Stopped simulator")


if __name__ == "__main__":
    main()

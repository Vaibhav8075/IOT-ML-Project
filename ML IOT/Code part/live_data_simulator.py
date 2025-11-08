# live_data_simulator.py
import csv
import random
import time
import os
import pandas as pd

OUTFILE = "fire_sensor_data.csv"
MAX_ROWS = 300  # ✅ ❌ CSV will never exceed 300 rows

HEADER = ["Temperature","Humidity","Smoke","CO","Flame","Pressure","Motion","Label"]

if not os.path.exists(OUTFILE):
    with open(OUTFILE, "w", newline="") as f:
        csv.writer(f).writerow(HEADER)

def generate_row():
    temp = round(random.uniform(20, 200), 2)
    hum = round(random.uniform(20, 90), 2)
    smoke = round(random.uniform(0, 2000), 2)
    co = round(random.uniform(0, 50), 2)
    flame = random.choice([0, 1])
    pressure = round(random.uniform(990, 1016), 2)
    motion = random.choice([0,1])

    # Label Logic -> Simplified
    if flame == 1 or smoke > 900 or co > 35:
        label = 2
    elif smoke > 300 or co > 10 or temp > 80:
        label = 1
    else:
        label = 0

    return [temp, hum, smoke, co, flame, pressure, motion, label]

def main():
    print("Live data simulator started ✅")
    try:
        while True:
            row = generate_row()
            df = pd.read_csv(OUTFILE)
            df.loc[len(df)] = row
            df = df.tail(MAX_ROWS)  # ✅ keep only last rows
            df.to_csv(OUTFILE, index=False)
            print(f"Updated: Temp={row[0]} Smoke={row[2]} CO={row[3]} Label={row[-1]}")
            time.sleep(2)
    except KeyboardInterrupt:
        print("Stopped simulator")

if __name__ == "__main__":
    main()

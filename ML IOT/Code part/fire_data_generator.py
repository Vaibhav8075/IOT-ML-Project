# fire_data_generator.py
import csv
import random

OUTFILE = "fire_sensor_data.csv"
N_PER_CLASS = 1500

def gen_normal():
    return {
        "Temperature": round(random.uniform(18, 30), 2),
        "Humidity": round(random.uniform(30, 60), 2),
        "Smoke": round(random.uniform(0, 80), 2),
        "CO": round(random.uniform(0, 3), 2),
        "Flame": 0.0,
        "Pressure": round(random.uniform(1008, 1015), 2),
        "Motion": random.choice([0,1]),
        "Label": 0
    }

def gen_cooking():
    return {
        "Temperature": round(random.uniform(30, 70), 2),
        "Humidity": round(random.uniform(45, 90), 2),
        "Smoke": round(random.uniform(150, 800), 2),
        "CO": round(random.uniform(0, 5), 2),
        "Flame": random.choice([0.0, 0.1]),
        "Pressure": round(random.uniform(1008, 1016), 2),
        "Motion": 1,
        "Label": 0
    }

def gen_electrical_fault():
    return {
        "Temperature": round(random.uniform(35, 95), 2),
        "Humidity": round(random.uniform(20, 60), 2),
        "Smoke": round(random.uniform(20, 450), 2),
        "CO": round(random.uniform(1, 10), 2),
        "Flame": random.choice([0.0, 0.2]),
        "Pressure": round(random.uniform(1004, 1012), 2),
        "Motion": random.choice([0,1]),
        "Label": 1
    }

def gen_smoldering():
    return {
        "Temperature": round(random.uniform(40, 100), 2),
        "Humidity": round(random.uniform(10, 50), 2),
        "Smoke": round(random.uniform(300, 900), 2),
        "CO": round(random.uniform(5, 25), 2),
        "Flame": random.choice([0.0, 0.3]),
        "Pressure": round(random.uniform(1000, 1010), 2),
        "Motion": random.choice([0,1]),
        "Label": 1
    }

def gen_open_flame():
    return {
        "Temperature": round(random.uniform(80, 200), 2),
        "Humidity": round(random.uniform(5, 40), 2),
        "Smoke": round(random.uniform(600, 2000), 2),
        "CO": round(random.uniform(10, 60), 2),
        "Flame": 1.0,
        "Pressure": round(random.uniform(990, 1008), 2),
        "Motion": random.choice([0,1]),
        "Label": 2
    }

def main():
    rows = []
    for _ in range(N_PER_CLASS):
        rows.append(gen_normal())
        rows.append(gen_cooking())
        rows.append(gen_electrical_fault())
        rows.append(gen_smoldering())
        rows.append(gen_open_flame())

    random_order = rows[:]
    random.shuffle(random_order)

    header = ["Temperature","Humidity","Smoke","CO","Flame","Pressure","Motion","Label"]
    with open(OUTFILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for r in random_order:
            writer.writerow(r)
    print(f" Wrote {len(random_order)} rows to {OUTFILE}")

if __name__ == "__main__":
    main()

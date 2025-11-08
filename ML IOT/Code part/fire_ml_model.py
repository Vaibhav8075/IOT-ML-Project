import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

def main():
    df = pd.read_csv("fire_sensor_data.csv")

    # ✅ Required sensor columns
    required_cols = ["Temperature", "Humidity", "Smoke", "CO", "Flame", "Pressure", "Motion"]

    # ✅ If some sensors are missing, auto-generate fake values
    for col in required_cols:
        if col not in df.columns:
            if col == "Pressure":
                df[col] = np.random.uniform(950, 1050, len(df))
            elif col == "Motion":
                df[col] = np.random.randint(0, 2, len(df))
            else:
                df[col] = 0

    # ✅ If no Fire label exists → create a smart rule-based label
    if "Fire" not in df.columns:
        df["Fire"] = np.where(
            (df["Smoke"] > 300) | 
            (df["CO"] > 300) | 
            (df["Flame"] == 1),
            1, 0
        )

    # ✅ Features & target
    X = df[required_cols]
    y = df["Fire"]

    # ✅ Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # ✅ ML Model
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    # ✅ Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # ✅ Save model
    joblib.dump(model, "fire_detection_model.pkl")

    print("✅ Model Training Complete!")
    print(f"🔥 Accuracy: {accuracy:.3f}")

if __name__ == "__main__":
    main()
    
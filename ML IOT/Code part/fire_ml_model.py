# fire_ml_model.py
# Trains a Random Forest classifier on sensor data matching actual ESP32 output.
# Features  : Temperature, Humidity, Smoke_ADC, CO_ADC, Flame, LDR_ADC, LDR_Flicker, Motion
# Labels    : 0 = Normal   1 = Warning   2 = Fire
# No Pressure column — we have no pressure sensor.

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, classification_report,
    confusion_matrix, ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt
import joblib
import os

CSV_FILE   = "fire_sensor_data.csv"
MODEL_FILE = "fire_detection_model.pkl"

FEATURES = [
    "Temperature",
    "Humidity",
    "Smoke_ADC",
    "CO_ADC",
    "Flame",
    "LDR_ADC",
    "LDR_Flicker",
    "Motion"
]

LABEL_NAMES = {0: "Normal", 1: "Warning", 2: "Fire"}

# ── Load data ─────────────────────────────────────────────────────────────────

def load_data():
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(
            f"{CSV_FILE} not found. Run fire_data_generator.py first."
        )
    df = pd.read_csv(CSV_FILE)

    missing = [c for c in FEATURES + ["Label"] if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")

    print(f"Loaded {len(df)} rows from {CSV_FILE}")
    print(f"Label distribution:\n{df['Label'].value_counts().sort_index()}\n")
    return df

# ── Train ─────────────────────────────────────────────────────────────────────

def train(df):
    X = df[FEATURES].values
    y = df["Label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=2,
        class_weight="balanced",   # handles any slight class imbalance
        random_state=42,
        n_jobs=-1
    )

    # 5-fold cross-validation on training set
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="accuracy")
    print(f"Cross-validation accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    model.fit(X_train, y_train)

    return model, X_test, y_test

# ── Evaluate ──────────────────────────────────────────────────────────────────

def evaluate(model, X_test, y_test):
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"\nTest Accuracy : {acc:.4f}\n")
    print("Classification Report:")
    print(classification_report(
        y_test, y_pred,
        target_names=[LABEL_NAMES[i] for i in sorted(LABEL_NAMES)]
    ))

    # Confusion matrix plot
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=[LABEL_NAMES[i] for i in sorted(LABEL_NAMES)]
    )
    fig, ax = plt.subplots(figsize=(6, 5))
    disp.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title("Confusion Matrix — Fire Detection Model")
    plt.tight_layout()
    plt.savefig("confusion_matrix.png", dpi=150)
    plt.close()
    print("Saved confusion_matrix.png")

    # Feature importance plot
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(range(len(FEATURES)), importances[indices], color="#E05C35")
    ax.set_xticks(range(len(FEATURES)))
    ax.set_xticklabels([FEATURES[i] for i in indices], rotation=30, ha="right")
    ax.set_title("Feature Importances")
    ax.set_ylabel("Importance")
    plt.tight_layout()
    plt.savefig("feature_importance.png", dpi=150)
    plt.close()
    print("Saved feature_importance.png")

    return acc

# ── Quick inference test ──────────────────────────────────────────────────────

def inference_test(model):
    """
    Spot-check the model against hand-crafted edge cases.
    Helps catch obvious labelling or scaling bugs before deployment.
    """
    tests = [
        # (label, description, feature_values)
        (0, "Normal room",        [24.0, 50.0, 150.0,  200.0, 0, 1800.0,  10.0, 1]),
        (0, "Cooking (steam)",    [55.0, 80.0, 1800.0, 300.0, 0, 2000.0,  15.0, 1]),
        (1, "Electrical fault",   [75.0, 35.0, 2000.0, 1500.0, 0, 1600.0, 40.0, 0]),
        (1, "Smoldering (early)", [90.0, 25.0, 3000.0, 2500.0, 0, 400.0,  80.0, 0]),
        (2, "Open flame",         [160.0, 12.0, 4000.0, 3800.0, 1, 100.0, 700.0, 1]),
    ]

    print("\nInference spot-check:")
    print(f"  {'Description':<22} Expected     Predicted")
    print("  " + "-" * 50)
    all_pass = True
    for expected, desc, feats in tests:
        pred = int(model.predict([feats])[0])
        match = "✓" if pred == expected else "✗"
        if pred != expected:
            all_pass = False
        print(f"  {desc:<22} {LABEL_NAMES[expected]:<12} {LABEL_NAMES[pred]}  {match}")

    if all_pass:
        print("\nAll spot-checks passed.")
    else:
        print("\nSome spot-checks failed — review thresholds in fire_data_generator.py")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    df = load_data()
    model, X_test, y_test = train(df)
    evaluate(model, X_test, y_test)
    inference_test(model)
    joblib.dump(model, MODEL_FILE)
    print(f"\nModel saved to {MODEL_FILE}")
    print("Features the model expects (in order):")
    for i, f in enumerate(FEATURES):
        print(f"  [{i}] {f}")

if __name__ == "__main__":
    main()
import os

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "fire_sensor_data.csv")
MODEL_FILE = os.path.join(BASE_DIR, "fire_detection_model.pkl")
SCALER_FILE = os.path.join(BASE_DIR, "fire_scaler.pkl")
CONFUSION_MATRIX_FILE = os.path.join(BASE_DIR, "confusion_matrix.png")
FEATURE_IMPORTANCE_FILE = os.path.join(BASE_DIR, "feature_importance.png")

FEATURES = [
    "Temperature",
    "Humidity",
    "CO_ADC",
    "H2_Raw",
    "PM25",
]

REQUIRED_COLUMNS = [
    "Temperature",
    "Humidity",
    "CO_ADC",
    "LDR_ADC",
    "Label",
]

LABEL_NAMES = {0: "Normal", 1: "Warning", 2: "Fire"}


def load_data():
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(
            f"{CSV_FILE} not found. Run fire_data_generator.py first."
        )

    df = pd.read_csv(CSV_FILE)
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")

    print(f"Loaded {len(df)} rows from {CSV_FILE}")
    print(f"Label distribution:\n{df['Label'].value_counts().sort_index()}\n")
    return df


def build_feature_frame(df):
    return pd.DataFrame(
        {
            "Temperature": df["Temperature"],
            "Humidity": df["Humidity"],
            "CO_ADC": df["CO_ADC"],
            # Match sensor_receiver.py: H2 is proxied from CO, PM2.5 from LDR.
            "H2_Raw": df["CO_ADC"],
            "PM25": df["LDR_ADC"],
        }
    )


def train(df):
    x_values = build_feature_frame(df).values
    y_values = df["Label"].values

    x_train, x_test, y_train, y_test = train_test_split(
        x_values,
        y_values,
        test_size=0.2,
        random_state=42,
        stratify=y_values,
    )

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    model = RandomForestClassifier(
        n_estimators=5,
        max_depth=2,
        min_samples_leaf=800,
        class_weight="balanced",
        random_state=42,
        # Keep training single-process so it works reliably on locked-down
        # Windows environments where multiprocessing pipes may be blocked.
        n_jobs=1,
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, x_train_scaled, y_train, cv=cv, scoring="accuracy")
    print(f"Cross-validation accuracy: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")

    model.fit(x_train_scaled, y_train)
    return model, scaler, x_test_scaled, y_test


def evaluate(model, x_test, y_test):
    y_pred = model.predict(x_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\nTest Accuracy: {accuracy:.4f}\n")
    print("Classification Report:")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=[LABEL_NAMES[index] for index in sorted(LABEL_NAMES)],
            zero_division=0,
        )
    )

    confusion = confusion_matrix(y_test, y_pred)
    display = ConfusionMatrixDisplay(
        confusion_matrix=confusion,
        display_labels=[LABEL_NAMES[index] for index in sorted(LABEL_NAMES)],
    )
    fig, ax = plt.subplots(figsize=(6, 5))
    display.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title("Confusion Matrix - Fire Detection Model")
    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_FILE, dpi=150)
    plt.close(fig)
    print(f"Saved {CONFUSION_MATRIX_FILE}")

    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(range(len(FEATURES)), importances[indices], color="#E05C35")
    ax.set_xticks(range(len(FEATURES)))
    ax.set_xticklabels([FEATURES[index] for index in indices], rotation=30, ha="right")
    ax.set_title("Feature Importances")
    ax.set_ylabel("Importance")
    plt.tight_layout()
    plt.savefig(FEATURE_IMPORTANCE_FILE, dpi=150)
    plt.close(fig)
    print(f"Saved {FEATURE_IMPORTANCE_FILE}")

    return accuracy


def inference_test(model, scaler):
    """
    Spot-check the model against hand-crafted edge cases.
    Helps catch obvious labeling or scaling bugs before deployment.
    """
    tests = [
        (0, "Normal room", [24.0, 50.0, 200.0, 200.0, 1800.0]),
        (0, "Cooking (steam)", [55.0, 80.0, 300.0, 300.0, 2000.0]),
        (1, "Electrical fault", [75.0, 35.0, 1500.0, 1500.0, 1600.0]),
        (1, "Smoldering (early)", [90.0, 25.0, 2500.0, 2500.0, 400.0]),
        (2, "Open flame", [160.0, 12.0, 3800.0, 3800.0, 100.0]),
    ]

    print("\nInference spot-check:")
    print(f"  {'Description':<22} Expected     Predicted")
    print("  " + "-" * 50)

    all_passed = True
    for expected, description, features in tests:
        predicted = int(model.predict(scaler.transform([features]))[0])
        marker = "OK" if predicted == expected else "X"
        if predicted != expected:
            all_passed = False
        print(
            f"  {description:<22} {LABEL_NAMES[expected]:<12} "
            f"{LABEL_NAMES[predicted]}  {marker}"
        )

    if all_passed:
        print("\nAll spot-checks passed.")
    else:
        print("\nSome spot-checks failed; review thresholds in fire_data_generator.py")


def main():
    df = load_data()
    model, scaler, x_test, y_test = train(df)
    evaluate(model, x_test, y_test)
    inference_test(model, scaler)
    joblib.dump(model, MODEL_FILE)
    joblib.dump(scaler, SCALER_FILE)

    print(f"\nModel saved to {MODEL_FILE}")
    print(f"Scaler saved to {SCALER_FILE}")
    print("Features the model expects (in order):")
    for index, feature in enumerate(FEATURES):
        print(f"  [{index}] {feature}")


if __name__ == "__main__":
    main()

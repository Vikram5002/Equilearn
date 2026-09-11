"""Month 3: placement-probability classifier.

Baseline Logistic Regression + an XGBoost model, trained on the synthetic
student profiles enriched with the market_alignment_score from the feature
store. Whichever scores higher on held-out AUC is saved as the model the
dashboard loads.
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
STUDENTS_IN = ROOT / "data" / "raw" / "students" / "students.csv"
GAPS_IN = ROOT / "data" / "processed" / "student_skill_gaps.csv"

MODEL_OUT = ROOT / "data" / "processed" / "placement_model.joblib"
METRICS_OUT = ROOT / "data" / "processed" / "model_metrics.json"

FEATURES = [
    "cgpa", "projects_count", "certifications_count", "internships_count",
    "skill_count", "market_alignment_score",
]


def build_training_table() -> pd.DataFrame:
    students = pd.read_csv(STUDENTS_IN)
    gaps = pd.read_csv(GAPS_IN)
    df = students.merge(gaps[["student_id", "market_alignment_score", "skill_count"]],
                         on="student_id")
    return df


def train(df: pd.DataFrame):
    X = df[FEATURES]
    y = df["placed"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    scaler = StandardScaler().fit(X_train)
    X_train_s, X_test_s = scaler.transform(X_train), scaler.transform(X_test)

    candidates = {
        "logistic_regression": LogisticRegression(max_iter=1000, random_state=42),
        "xgboost": XGBClassifier(
            n_estimators=200, max_depth=3, learning_rate=0.1,
            random_state=42, eval_metric="logloss",
        ),
    }

    results = {}
    for name, model in candidates.items():
        model.fit(X_train_s, y_train)
        proba = model.predict_proba(X_test_s)[:, 1]
        preds = model.predict(X_test_s)
        results[name] = {
            "model": model,
            "auc": roc_auc_score(y_test, proba),
            "accuracy": accuracy_score(y_test, preds),
            "report": classification_report(y_test, preds, output_dict=True),
        }
        print(f"{name}: AUC={results[name]['auc']:.3f}  accuracy={results[name]['accuracy']:.3f}")

    best_name = max(results, key=lambda n: results[n]["auc"])
    best = results[best_name]
    print(f"\nBest model: {best_name} (AUC={best['auc']:.3f})")

    if hasattr(best["model"], "feature_importances_"):
        importances = dict(zip(FEATURES, best["model"].feature_importances_.tolist()))
    elif hasattr(best["model"], "coef_"):
        importances = dict(zip(FEATURES, best["model"].coef_[0].tolist()))
    else:
        importances = {}
    print("Feature importances:", json.dumps(importances, indent=2))

    joblib.dump({"model": best["model"], "scaler": scaler, "features": FEATURES}, MODEL_OUT)

    metrics = {
        "best_model": best_name,
        "auc": best["auc"],
        "accuracy": best["accuracy"],
        "feature_importances": importances,
        "all_models": {n: {"auc": r["auc"], "accuracy": r["accuracy"]} for n, r in results.items()},
    }
    METRICS_OUT.write_text(json.dumps(metrics, indent=2))
    print(f"\nSaved model -> {MODEL_OUT}")
    print(f"Saved metrics -> {METRICS_OUT}")


def main():
    df = build_training_table()
    train(df)


if __name__ == "__main__":
    main()

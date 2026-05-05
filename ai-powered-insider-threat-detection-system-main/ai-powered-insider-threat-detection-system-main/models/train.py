from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
MODEL_DIR = ROOT_DIR / "models"
DASHBOARD_DIR = ROOT_DIR / "dashboard"

sys.path.insert(0, str(ROOT_DIR / "features"))
from merge_features import merge_features

MODEL_DIR.mkdir(exist_ok=True)
DASHBOARD_DIR.mkdir(exist_ok=True)


def minmax(values):
    values = np.asarray(values, dtype=float)
    value_range = values.max() - values.min()
    if value_range == 0:
        return np.zeros_like(values)
    return (values - values.min()) / value_range


def safe_roc_auc(y_true, scores):
    return roc_auc_score(y_true, scores) if pd.Series(y_true).nunique() == 2 else np.nan


def build_html_report(scores: pd.DataFrame, metrics: pd.DataFrame) -> None:
    top_users = scores.sort_values("hybrid_score", ascending=False).head(10).copy()
    display_columns = [
        "rank",
        "user",
        "risk_label",
        "hybrid_score",
        "supervised_probability",
        "unsupervised_ensemble",
        "is_red_team",
    ]
    top_users["rank"] = range(1, len(top_users) + 1)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Insider Threat Hybrid Anomaly Results</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #18202a; background: #f6f8fb; }}
    h1, h2 {{ margin-bottom: 8px; }}
    .summary {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 16px 0; }}
    .metric {{ background: white; border: 1px solid #d9e0ea; border-radius: 8px; padding: 12px 16px; min-width: 150px; }}
    .metric strong {{ display: block; font-size: 22px; }}
    table {{ border-collapse: collapse; width: 100%; background: white; margin: 12px 0 24px; }}
    th, td {{ border: 1px solid #d9e0ea; padding: 8px 10px; text-align: left; }}
    th {{ background: #eaf0f7; }}
    tr:nth-child(even) {{ background: #f9fbfd; }}
  </style>
</head>
<body>
  <h1>Hybrid Insider Threat Anomaly Results</h1>
  <p>Final risk combines supervised Random Forest probability with unsupervised Isolation Forest, One-Class SVM, and autoencoder anomaly scores.</p>
  <div class="summary">
    <div class="metric"><span>Total users</span><strong>{len(scores)}</strong></div>
    <div class="metric"><span>Flagged users</span><strong>{int(scores["hybrid_prediction"].sum())}</strong></div>
    <div class="metric"><span>Known red-team users</span><strong>{int(scores["is_red_team"].sum())}</strong></div>
  </div>
  <h2>Top Anomalous Users</h2>
  {top_users[display_columns].to_html(index=False, float_format=lambda value: f"{value:.3f}")}
  <h2>Model Metrics</h2>
  {metrics.to_html(index=False, float_format=lambda value: f"{value:.3f}")}
</body>
</html>
"""
    (DASHBOARD_DIR / "anomaly_results.html").write_text(html, encoding="utf-8")


def train_models() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = merge_features()
    if df.empty:
        raise ValueError("No feature rows were created. Check the CSV files in data/.")

    y = df["is_red_team"].astype(int)
    X = df.drop(columns=["user", "is_red_team"], errors="ignore")
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, MODEL_DIR / "feature_scaler.pkl")

    contamination = min(0.25, max(0.05, y.mean() if y.sum() else 0.1))
    iso = IsolationForest(contamination=contamination, random_state=42)
    iso.fit(X_scaled)
    iso_scores = -iso.score_samples(X_scaled)
    joblib.dump(iso, MODEL_DIR / "isolation_forest.pkl")

    svm = OneClassSVM(nu=contamination, kernel="rbf", gamma="scale")
    svm.fit(X_scaled)
    svm_scores = -svm.decision_function(X_scaled)
    joblib.dump(svm, MODEL_DIR / "oneclass_svm.pkl")

    auto = MLPRegressor(hidden_layer_sizes=(8, 4, 8), max_iter=1000, random_state=42)
    auto.fit(X_scaled, X_scaled)
    auto_recon = np.mean((X_scaled - auto.predict(X_scaled)) ** 2, axis=1)
    joblib.dump(auto, MODEL_DIR / "autoencoder.pkl")

    can_train_supervised = y.nunique() == 2 and y.value_counts().min() >= 2
    if can_train_supervised:
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled,
            y,
            test_size=0.35,
            random_state=42,
            stratify=y,
        )
        supervised = RandomForestClassifier(
            n_estimators=300,
            max_depth=6,
            class_weight="balanced",
            random_state=42,
        )
        supervised.fit(X_train, y_train)
        supervised_probability = supervised.predict_proba(X_scaled)[:, 1]
        test_probability = supervised.predict_proba(X_test)[:, 1]
        test_prediction = (test_probability >= 0.5).astype(int)
    else:
        X_test, y_test = X_scaled, y
        supervised = DummyClassifier(strategy="constant", constant=0)
        supervised.fit(X_scaled, y)
        supervised_probability = np.zeros(len(y), dtype=float)
        test_probability = supervised_probability
        test_prediction = np.zeros(len(y), dtype=int)
    joblib.dump(supervised, MODEL_DIR / "supervised_random_forest.pkl")

    unsupervised_ensemble = np.mean(
        [minmax(iso_scores), minmax(svm_scores), minmax(auto_recon)],
        axis=0,
    )
    hybrid_score = 0.45 * unsupervised_ensemble + 0.55 * supervised_probability
    threshold = float(np.percentile(hybrid_score, 90))
    hybrid_prediction = (hybrid_score >= threshold).astype(int)
    risk_label = np.where(
        hybrid_score >= threshold,
        "High",
        np.where(hybrid_score >= np.percentile(hybrid_score, 70), "Medium", "Low"),
    )

    scores = pd.DataFrame({
        "user": df["user"],
        "is_red_team": y,
        "isolation_forest": iso_scores,
        "oneclass_svm": svm_scores,
        "autoencoder": auto_recon,
        "unsupervised_ensemble": unsupervised_ensemble,
        "supervised_probability": supervised_probability,
        "hybrid_score": hybrid_score,
        "hybrid_threshold": threshold,
        "hybrid_prediction": hybrid_prediction,
        "risk_label": risk_label,
    })
    scores.to_csv(DATA_DIR / "anomaly_scores.csv", index=False)

    metrics = pd.DataFrame([
        {
            "model": "supervised_random_forest",
            "accuracy": accuracy_score(y_test, test_prediction),
            "precision": precision_score(y_test, test_prediction, zero_division=0),
            "recall": recall_score(y_test, test_prediction, zero_division=0),
            "f1": f1_score(y_test, test_prediction, zero_division=0),
            "roc_auc": safe_roc_auc(y_test, test_probability),
        },
        {
            "model": "hybrid_supervised_unsupervised",
            "accuracy": accuracy_score(y, hybrid_prediction),
            "precision": precision_score(y, hybrid_prediction, zero_division=0),
            "recall": recall_score(y, hybrid_prediction, zero_division=0),
            "f1": f1_score(y, hybrid_prediction, zero_division=0),
            "roc_auc": safe_roc_auc(y, hybrid_score),
        },
    ])
    metrics.to_csv(DATA_DIR / "hybrid_model_results.csv", index=False)
    build_html_report(scores, metrics)
    return scores, metrics


if __name__ == "__main__":
    train_models()
    print("Models trained and scores saved to data/anomaly_scores.csv")
    print("Hybrid model results saved to data/hybrid_model_results.csv")
    print("HTML report saved to dashboard/anomaly_results.html")

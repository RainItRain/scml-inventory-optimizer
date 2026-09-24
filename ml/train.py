"""
Train the demand-forecasting model and produce all deployment artifacts.

Pipeline:
  1. Load data (generates a synthetic dataset if none is found).
  2. Build leakage-free features (lag / rolling / calendar / encoded categoricals).
  3. Chronological train/test split (train on the past, validate on the future).
  4. Train a RandomForestRegressor and report MAE / RMSE / MAPE / R2.
  5. Run inventory optimization on the test period.
  6. Persist: model, encoders, feature list, metrics.json, results snapshot.

Usage:
    python ml/train.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import build_features, feature_columns  # noqa: E402
from optimize import optimize_inventory, summarize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "retail_store_inventory.csv"
ARTIFACT_DIR = ROOT / "ml" / "artifacts"


def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        print("Dataset not found — generating a synthetic one...")
        subprocess.run(
            [sys.executable, str(ROOT / "data" / "generate_dataset.py")], check=True
        )
    print(f"Loading {DATA_PATH}")
    return pd.read_csv(DATA_PATH, parse_dates=["Date"])


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()
    print(f"Rows: {len(df):,}")

    df_encoded, le_store, le_product = build_features(df)
    feat_cols = feature_columns(df_encoded)
    print(f"Features: {len(feat_cols)}  |  Rows after feature build: {len(df_encoded):,}")

    X = df_encoded[feat_cols]
    y = df_encoded["Units Sold"]

    # Chronological split: past -> train, future -> test (no leakage).
    cutoff = df_encoded["Date"].quantile(0.8, interpolation="nearest")
    train_mask = df_encoded["Date"] <= cutoff
    test_mask = df_encoded["Date"] > cutoff
    X_train, X_test = X[train_mask], X[test_mask]
    y_train, y_test = y[train_mask], y[test_mask]
    print(f"Train: {len(X_train):,} (<= {cutoff.date()})  Test: {len(X_test):,} (> {cutoff.date()})")

    model = RandomForestRegressor(
        n_estimators=150, max_depth=14, min_samples_leaf=8,
        random_state=42, n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mape = float((np.abs((y_test - y_pred) / y_test.replace(0, np.nan))).mean() * 100)
    r2 = r2_score(y_test, y_pred)
    print(f"MAE={mae:.2f}  RMSE={rmse:.2f}  MAPE={mape:.2f}%  R2={r2:.3f}")

    # ---- Inventory optimization on the test period ----
    results = X_test.copy()
    results["Date"] = df_encoded.loc[test_mask, "Date"].values
    results["Actual_Sales"] = y_test.values
    results["Predicted_Demand"] = y_pred.round(1)
    results["Inventory Level"] = df_encoded.loc[test_mask, "Inventory Level"].values
    results["Price"] = df_encoded.loc[test_mask, "Price"].values
    results["Store ID"] = le_store.inverse_transform(df_encoded.loc[test_mask, "Store_ID_enc"])
    results["Product ID"] = le_product.inverse_transform(df_encoded.loc[test_mask, "Product_ID_enc"])
    results["Category"] = _recover_category(df_encoded, test_mask)

    results = optimize_inventory(results)
    kpis = summarize(results)
    print("KPIs:", json.dumps(kpis, indent=2))

    # ---- Top feature importances ----
    importances = (
        pd.Series(model.feature_importances_, index=feat_cols)
        .sort_values(ascending=False).head(12)
    )
    feat_importance = [{"feature": k, "importance": round(float(v), 4)}
                       for k, v in importances.items()]

    # ---- Persist artifacts ----
    joblib.dump(model, ARTIFACT_DIR / "model.pkl", compress=3)
    joblib.dump(le_store, ARTIFACT_DIR / "store_encoder.pkl")
    joblib.dump(le_product, ARTIFACT_DIR / "product_encoder.pkl")
    joblib.dump(feat_cols, ARTIFACT_DIR / "feature_cols.pkl")

    metrics = {
        "mae": round(mae, 2), "rmse": round(rmse, 2),
        "mape": round(mape, 2), "r2": round(r2, 3),
        "train_rows": int(len(X_train)), "test_rows": int(len(X_test)),
        "n_features": len(feat_cols), "cutoff_date": str(cutoff.date()),
        "model": "RandomForestRegressor(n_estimators=200, max_depth=16)",
        "kpis": kpis, "feature_importance": feat_importance,
    }
    (ARTIFACT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))

    # Compact results snapshot the API serves for the dashboard.
    snapshot_cols = [
        "Store ID", "Product ID", "Category", "Date", "Actual_Sales",
        "Predicted_Demand", "Inventory Level", "Price", "Safety_Stock",
        "Reorder_Point", "Days_of_Cover", "Stock_Status",
        "Recommended_Order_Qty", "Potential_Lost_Revenue",
    ]
    snapshot = results[snapshot_cols].copy()
    snapshot["Date"] = pd.to_datetime(snapshot["Date"]).dt.strftime("%Y-%m-%d")
    snapshot.round(2).to_json(ARTIFACT_DIR / "results_snapshot.json", orient="records")

    print(f"\nSaved artifacts to {ARTIFACT_DIR}")


def _recover_category(df_encoded: pd.DataFrame, test_mask) -> np.ndarray:
    cat_cols = [c for c in df_encoded.columns if c.startswith("Category_")]
    sub = df_encoded.loc[test_mask, cat_cols]
    return np.where(
        sub.any(axis=1),
        sub.idxmax(axis=1).str.replace("Category_", "", regex=False),
        "Groceries",  # the drop_first baseline category
    )


if __name__ == "__main__":
    main()

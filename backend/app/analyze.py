"""
On-the-fly analysis of a user-uploaded dataset.

Trains a fresh (lightweight) demand-forecasting model on the uploaded CSV using
the same leakage-free pipeline as the main project, then runs inventory
optimization and returns metrics + KPIs + recommendations in the same shape as
`/api/metrics` (so the frontend can reuse its components).

Kept deliberately light (fewer trees, row cap) so it runs within a free-tier
container's CPU/memory budget.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parent.parent.parent
for p in (ROOT / "ml", ROOT / "data"):
    sys.path.insert(0, str(p))

from features import build_features, feature_columns  # noqa: E402
from optimize import optimize_inventory, summarize  # noqa: E402

REQUIRED_COLUMNS = [
    "Date", "Store ID", "Product ID", "Category", "Region",
    "Inventory Level", "Units Sold", "Price", "Weather Condition", "Seasonality",
]

MAX_ROWS = 60_000
UPLOAD_RF = dict(n_estimators=80, max_depth=12, min_samples_leaf=10)

REC_COLS = [
    "Store ID", "Product ID", "Category", "Date", "Actual_Sales",
    "Predicted_Demand", "Inventory Level", "Price", "Safety_Stock",
    "Reorder_Point", "Days_of_Cover", "Stock_Status",
    "Recommended_Order_Qty", "Potential_Lost_Revenue",
]


class AnalyzeError(Exception):
    """Raised for user-facing validation problems (returned as HTTP 400)."""


def analyze_dataframe(df: pd.DataFrame) -> dict:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise AnalyzeError(
            f"Missing required column(s): {', '.join(missing)}. "
            "Download the sample template to see the expected format."
        )

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for col in ["Inventory Level", "Units Sold", "Price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Date", "Units Sold", "Inventory Level", "Price"])

    if len(df) > MAX_ROWS:
        df = df.sort_values("Date").tail(MAX_ROWS)
    if len(df) < 300:
        raise AnalyzeError(
            "Not enough valid rows to analyze (need at least ~300 daily records "
            "across your stores/products)."
        )

    # Leakage-free feature engineering (lags/rolling need history per series).
    df_encoded, le_store, le_product = build_features(df)
    if len(df_encoded) < 100:
        raise AnalyzeError(
            "After building time-series features too few rows remain. Each "
            "store-product series needs ~2+ weeks of consecutive daily history."
        )

    # Only numeric/boolean features (drop stray text columns the user may add).
    feat_cols = [
        c for c in feature_columns(df_encoded)
        if pd.api.types.is_numeric_dtype(df_encoded[c])
        or pd.api.types.is_bool_dtype(df_encoded[c])
    ]
    X = df_encoded[feat_cols].fillna(0)
    y = df_encoded["Units Sold"]

    # Chronological split; fall back to a positional split on tiny datasets.
    cutoff = df_encoded["Date"].quantile(0.8, interpolation="nearest")
    train_mask = (df_encoded["Date"] <= cutoff).values
    test_mask = (df_encoded["Date"] > cutoff).values
    if train_mask.sum() < 50 or test_mask.sum() < 20:
        split = int(len(X) * 0.8)
        train_mask = np.zeros(len(X), dtype=bool)
        test_mask = np.zeros(len(X), dtype=bool)
        train_mask[:split] = True
        test_mask[split:] = True

    model = RandomForestRegressor(**UPLOAD_RF, random_state=42, n_jobs=-1)
    model.fit(X[train_mask], y[train_mask])
    y_test = y[test_mask]
    y_pred = model.predict(X[test_mask])

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    with np.errstate(divide="ignore", invalid="ignore"):
        mape = float((np.abs((y_test - y_pred) / y_test.replace(0, np.nan))).mean() * 100)
    r2 = float(r2_score(y_test, y_pred))

    # Inventory optimization on the held-out period.
    test_idx = df_encoded.index[test_mask]
    results = X[test_mask].copy()
    results["Date"] = df_encoded.loc[test_idx, "Date"].values
    results["Actual_Sales"] = y_test.values
    results["Predicted_Demand"] = y_pred.round(1)
    results["Inventory Level"] = df_encoded.loc[test_idx, "Inventory Level"].values
    results["Price"] = df_encoded.loc[test_idx, "Price"].values
    results["Store ID"] = le_store.inverse_transform(df_encoded.loc[test_idx, "Store_ID_enc"])
    results["Product ID"] = le_product.inverse_transform(df_encoded.loc[test_idx, "Product_ID_enc"])
    results["Category"] = _recover_category(df_encoded.loc[test_idx])
    results = optimize_inventory(results)

    kpis = summarize(results)
    importances = (
        pd.Series(model.feature_importances_, index=feat_cols)
        .sort_values(ascending=False).head(12)
    )
    feat_importance = [
        {"feature": k, "importance": round(float(v), 4)} for k, v in importances.items()
    ]

    recs = (
        results[results["Recommended_Order_Qty"] > 0]
        .nlargest(12, "Potential_Lost_Revenue")[REC_COLS]
        .copy()
    )
    recs["Date"] = pd.to_datetime(recs["Date"]).dt.strftime("%Y-%m-%d")

    return {
        "mae": round(mae, 2), "rmse": round(rmse, 2),
        "mape": round(mape, 2), "r2": round(r2, 3),
        "train_rows": int(train_mask.sum()), "test_rows": int(test_mask.sum()),
        "n_features": len(feat_cols),
        "cutoff_date": str(pd.to_datetime(df_encoded.loc[test_idx, "Date"]).min().date()),
        "model": f"RandomForestRegressor(n_estimators={UPLOAD_RF['n_estimators']}, "
                 f"max_depth={UPLOAD_RF['max_depth']})",
        "kpis": kpis,
        "feature_importance": feat_importance,
        "recommendations": recs.round(2).to_dict(orient="records"),
    }


def _recover_category(df_encoded: pd.DataFrame) -> np.ndarray:
    cat_cols = [c for c in df_encoded.columns if c.startswith("Category_")]
    if not cat_cols:
        return np.array(["(category)"] * len(df_encoded))
    sub = df_encoded[cat_cols]
    return np.where(
        sub.any(axis=1),
        sub.idxmax(axis=1).astype(str).str.replace("Category_", "", regex=False),
        "(baseline)",
    )


def sample_template_csv() -> str:
    """A small, valid example dataset users can download and mimic."""
    import generate_dataset  # from ROOT/data on sys.path

    df = generate_dataset.generate(stores=2, products=3, days=120)
    return df.to_csv(index=False)

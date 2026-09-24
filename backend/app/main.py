"""
FastAPI service for the AI Inventory & Demand Optimization Platform.

Serves:
  - Model metrics + KPIs               GET  /api/metrics
  - Inventory dashboard rows (filter)  GET  /api/inventory
  - Top reorder recommendations        GET  /api/reorder-recommendations
  - What-if forecast + optimization    POST /api/simulate
  - Health check                       GET  /api/health

In production the built React app (frontend/dist) is served from "/".
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .schemas import Metrics, SimulationRequest, SimulationResponse

ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACT_DIR = ROOT / "ml" / "artifacts"
FRONTEND_DIST = ROOT / "frontend" / "dist"

app = FastAPI(
    title="AI Inventory & Demand Optimization API",
    description="Demand forecasting + inventory optimization for retail supply chains.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Store:
    """Lazily loads and caches ML artifacts."""

    def __init__(self) -> None:
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        missing = [f for f in ("model.pkl", "feature_cols.pkl", "metrics.json",
                               "results_snapshot.json")
                   if not (ARTIFACT_DIR / f).exists()]
        if missing:
            raise FileNotFoundError(
                f"Missing artifacts: {missing}. Run `python ml/train.py` first."
            )
        self.model = joblib.load(ARTIFACT_DIR / "model.pkl")
        self.feature_cols = joblib.load(ARTIFACT_DIR / "feature_cols.pkl")
        self.metrics = json.loads((ARTIFACT_DIR / "metrics.json").read_text())
        self.results = pd.read_json(ARTIFACT_DIR / "results_snapshot.json",
                                    convert_dates=False)
        self._loaded = True


store = Store()


@app.on_event("startup")
def _startup() -> None:
    try:
        store.load()
        print("Artifacts loaded.")
    except FileNotFoundError as exc:  # pragma: no cover - startup guard
        print(f"WARNING: {exc}")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "artifacts_loaded": store._loaded}


@app.get("/api/metrics", response_model=Metrics)
def get_metrics() -> dict:
    _ensure_loaded()
    return store.metrics


@app.get("/api/inventory")
def get_inventory(
    status: str | None = Query(None, description="HEALTHY | WARNING | CRITICAL"),
    store_id: str | None = None,
    category: str | None = None,
    sort_by: str = Query("Potential_Lost_Revenue"),
    limit: int = Query(100, ge=1, le=2000),
) -> dict:
    _ensure_loaded()
    df = store.results
    if status:
        df = df[df["Stock_Status"] == status.upper()]
    if store_id:
        df = df[df["Store ID"] == store_id]
    if category:
        df = df[df["Category"] == category]
    if sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=False)
    total = len(df)
    return {"total": int(total), "items": df.head(limit).to_dict(orient="records")}


@app.get("/api/reorder-recommendations")
def reorder_recommendations(limit: int = Query(15, ge=1, le=200)) -> dict:
    _ensure_loaded()
    df = store.results[store.results["Recommended_Order_Qty"] > 0]
    df = df.sort_values("Potential_Lost_Revenue", ascending=False).head(limit)
    return {"count": int(len(df)), "items": df.to_dict(orient="records")}


@app.get("/api/filters")
def get_filters() -> dict:
    _ensure_loaded()
    df = store.results
    return {
        "stores": sorted(df["Store ID"].unique().tolist()),
        "categories": sorted(df["Category"].unique().tolist()),
        "statuses": ["HEALTHY", "WARNING", "CRITICAL"],
    }


@app.post("/api/simulate", response_model=SimulationResponse)
def simulate(req: SimulationRequest) -> SimulationResponse:
    _ensure_loaded()
    row = _build_feature_row(req)
    X = pd.DataFrame([row])[store.feature_cols]
    predicted = float(store.model.predict(X)[0])

    # Optimization math mirrors ml/optimize.py for a single SKU.
    z = 1.65
    demand_std = max(req.rolling_mean_7 * 0.25, 1.0)  # proxy for demand variability
    avg_daily = max(predicted, 0.1)
    safety_stock = z * demand_std * np.sqrt(req.lead_time_days)
    reorder_point = avg_daily * req.lead_time_days + safety_stock
    days_of_cover = req.inventory_level / avg_daily
    ratio = req.inventory_level / reorder_point if reorder_point else 1.0

    status = "HEALTHY" if ratio >= 1.0 else "WARNING" if ratio >= 0.7 else "CRITICAL"
    lead_time_demand = avg_daily * req.lead_time_days
    shortfall = lead_time_demand - req.inventory_level
    rec_qty = int(round(max(reorder_point - req.inventory_level, 0))) if status != "HEALTHY" else 0
    lost_rev = round(max(shortfall, 0) * req.price, 2)

    return SimulationResponse(
        predicted_demand=round(predicted, 1),
        safety_stock=round(safety_stock, 1),
        reorder_point=round(reorder_point, 1),
        days_of_cover=round(days_of_cover, 1),
        stock_status=status,
        recommended_order_qty=rec_qty,
        potential_lost_revenue=lost_rev,
    )


def _build_feature_row(req: SimulationRequest) -> dict:
    """Construct a full feature vector from partial user inputs + sane defaults."""
    row = {c: 0 for c in store.feature_cols}
    rm7 = req.rolling_mean_7
    row.update({
        "Inventory Level": req.inventory_level,
        "Units Ordered": rm7,
        "Price": req.price,
        "Discount": req.discount,
        "Holiday/Promotion": int(req.is_holiday_promo),
        "Competitor Pricing": req.price * 1.02,
        "Month": 6, "DayOfWeek": 2, "WeekOfYear": 24, "IsWeekend": 0,
        "lag_7": req.lag_7, "lag_14": req.lag_7,
        "rolling_mean_7": rm7, "rolling_std_7": max(rm7 * 0.2, 1.0),
        "rolling_mean_30": rm7, "Store_ID_enc": 0, "Product_ID_enc": 0,
    })
    _set_dummy(row, "Category", req.category)
    _set_dummy(row, "Region", req.region)
    _set_dummy(row, "Weather Condition", req.weather)
    _set_dummy(row, "Seasonality", req.season)
    return row


def _set_dummy(row: dict, prefix: str, value: str) -> None:
    col = f"{prefix}_{value}"
    if col in row:
        row[col] = 1  # otherwise it's the dropped baseline category → all zeros


def _ensure_loaded() -> None:
    try:
        store.load()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# Serve the built frontend if it exists (single-container deployment).
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")

"""
Inventory optimization on top of demand forecasts.

Implements the standard supply-chain formulas:
  - Safety stock     = Z * sigma_demand * sqrt(lead_time)
  - Reorder point    = avg_daily_demand * lead_time + safety_stock
  - Stock status     = HEALTHY / WARNING / CRITICAL from inventory-to-reorder ratio
  - Recommended qty  = amount needed to return above the reorder point
  - Lost revenue     = shortfall over lead-time demand * unit price

Z = 1.65 corresponds to a ~95% service level.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_LEAD_TIME_DAYS = 3
DEFAULT_SERVICE_Z = 1.65  # ~95% service level


def optimize_inventory(
    results: pd.DataFrame,
    lead_time_days: int = DEFAULT_LEAD_TIME_DAYS,
    service_z: float = DEFAULT_SERVICE_Z,
    group_keys: tuple[str, str] = ("Store_ID_enc", "Product_ID_enc"),
) -> pd.DataFrame:
    """
    Expects a frame with columns:
        Predicted_Demand, Actual_Sales (optional), Inventory Level, Price,
        and the two group_keys.
    Returns the same frame enriched with optimization columns.
    """
    df = results.copy()
    gk = list(group_keys)

    demand_std = (
        df.groupby(gk)["Actual_Sales"].transform("std")
        if "Actual_Sales" in df.columns
        else df.groupby(gk)["Predicted_Demand"].transform("std")
    )
    demand_std = demand_std.fillna(df["Predicted_Demand"].std())

    avg_daily_demand = df.groupby(gk)["Predicted_Demand"].transform("mean")

    df["Safety_Stock"] = service_z * demand_std * np.sqrt(lead_time_days)
    df["Reorder_Point"] = avg_daily_demand * lead_time_days + df["Safety_Stock"]

    df["Reorder_Ratio"] = df["Inventory Level"] / df["Reorder_Point"].replace(0, np.nan)
    df["Days_of_Cover"] = df["Inventory Level"] / avg_daily_demand.replace(0, np.nan)

    df["Stock_Status"] = df["Reorder_Ratio"].apply(_categorize)

    lead_time_demand = avg_daily_demand * lead_time_days
    df["Stock_Shortfall"] = lead_time_demand - df["Inventory Level"]

    df["Recommended_Order_Qty"] = np.where(
        df["Stock_Status"].isin(["CRITICAL", "WARNING"]),
        (df["Reorder_Point"] - df["Inventory Level"]).clip(lower=0).round(),
        0,
    ).astype(int)

    df["Potential_Lost_Revenue"] = np.where(
        df["Stock_Shortfall"] > 0, df["Stock_Shortfall"] * df["Price"], 0.0
    ).round(2)

    return df


def _categorize(ratio: float) -> str:
    if pd.isna(ratio):
        return "HEALTHY"
    if ratio >= 1.0:
        return "HEALTHY"
    if ratio >= 0.7:
        return "WARNING"
    return "CRITICAL"


def summarize(df: pd.DataFrame) -> dict:
    """Aggregate KPIs for the dashboard."""
    status_counts = df["Stock_Status"].value_counts().to_dict()
    return {
        "total_skus": int(len(df)),
        "healthy": int(status_counts.get("HEALTHY", 0)),
        "warning": int(status_counts.get("WARNING", 0)),
        "critical": int(status_counts.get("CRITICAL", 0)),
        "total_potential_lost_revenue": float(round(df["Potential_Lost_Revenue"].sum(), 2)),
        "avg_days_of_cover": float(round(df["Days_of_Cover"].replace([np.inf, -np.inf], np.nan).dropna().mean(), 1)),
        "units_to_reorder": int(df["Recommended_Order_Qty"].sum()),
    }

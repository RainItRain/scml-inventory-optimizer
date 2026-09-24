"""
Feature engineering for demand forecasting.

Builds calendar, lag and rolling-window features per (store, product) time series.
All rolling/lag features are shifted so a row never sees its own or future sales
(prevents target leakage). This module is shared by training and inference.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CAT_COLS = ["Category", "Region", "Weather Condition", "Seasonality"]

# Columns that must never be used as model inputs (identifiers / target / leakage).
# "Units Ordered" and "Demand Forecast" are same-day proxies for the target and
# would leak the answer, so they are excluded — the model must forecast from
# history (lags, rolling means), price, calendar and categorical context.
DROP_ALWAYS = ["Units Sold", "Date", "Store ID", "Product ID",
               "Demand Forecast", "Units Ordered"]


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.month
    df["DayOfWeek"] = df["Date"].dt.dayofweek
    df["WeekOfYear"] = df["Date"].dt.isocalendar().week.astype(int)
    df["IsWeekend"] = (df["DayOfWeek"] >= 5).astype(int)
    return df


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """Lag & rolling stats per (store, product). shift() prevents leakage."""
    df = df.sort_values(["Store ID", "Product ID", "Date"]).reset_index(drop=True)
    grp = df.groupby(["Store ID", "Product ID"])["Units Sold"]

    # shift() keeps each row blind to its own/future sales; transform + shift(1)
    # inside the lambda keeps every rolling window within its own (store, product).
    df["lag_7"] = grp.shift(7)
    df["lag_14"] = grp.shift(14)
    df["rolling_mean_7"] = grp.transform(lambda s: s.shift(1).rolling(7).mean())
    df["rolling_std_7"] = grp.transform(lambda s: s.shift(1).rolling(7).std())
    df["rolling_mean_30"] = grp.transform(lambda s: s.shift(1).rolling(30).mean())
    return df


def build_features(df: pd.DataFrame, store_encoder=None, product_encoder=None):
    """
    Full feature pipeline. Returns (df_encoded, store_encoder, product_encoder).
    Pass fitted encoders at inference time; leave None to fit fresh (training).
    """
    from sklearn.preprocessing import LabelEncoder

    df = add_calendar_features(df)
    df = add_lag_features(df)
    df = df.dropna(subset=["lag_7", "lag_14", "rolling_mean_7", "rolling_std_7"]).reset_index(drop=True)

    if store_encoder is None:
        store_encoder = LabelEncoder().fit(df["Store ID"])
    if product_encoder is None:
        product_encoder = LabelEncoder().fit(df["Product ID"])

    df["Store_ID_enc"] = store_encoder.transform(df["Store ID"])
    df["Product_ID_enc"] = product_encoder.transform(df["Product ID"])

    df_encoded = pd.get_dummies(df, columns=CAT_COLS, drop_first=True)
    return df_encoded, store_encoder, product_encoder


def feature_columns(df_encoded: pd.DataFrame) -> list[str]:
    return [c for c in df_encoded.columns if c not in DROP_ALWAYS]

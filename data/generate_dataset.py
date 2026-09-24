"""
Synthetic retail inventory dataset generator.

Reproduces the schema of the Kaggle "Retail Store Inventory Forecasting" dataset
so the whole project runs end-to-end without any external download. The generated
data has realistic structure: per-(store, product) daily time series with trend,
weekly + yearly seasonality, promotion/holiday spikes, weather and price effects.

Usage:
    python data/generate_dataset.py --stores 5 --products 20 --days 730
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

CATEGORIES = ["Groceries", "Electronics", "Clothing", "Toys", "Furniture"]
REGIONS = ["North", "South", "East", "West"]
WEATHER = ["Sunny", "Rainy", "Cloudy", "Snowy"]
SEASONS = ["Spring", "Summer", "Autumn", "Winter"]


def _season_for_month(month: int) -> str:
    return {12: "Winter", 1: "Winter", 2: "Winter",
            3: "Spring", 4: "Spring", 5: "Spring",
            6: "Summer", 7: "Summer", 8: "Summer",
            9: "Autumn", 10: "Autumn", 11: "Autumn"}[month]


def generate(stores: int, products: int, days: int, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2022-01-01")
    dates = pd.date_range(start, periods=days, freq="D")
    day_index = np.arange(days)

    rows = []
    for s in range(1, stores + 1):
        store_id = f"S{s:03d}"
        region = REGIONS[(s - 1) % len(REGIONS)]
        store_level = rng.uniform(0.8, 1.4)  # store popularity multiplier

        for p in range(1, products + 1):
            product_id = f"P{p:04d}"
            category = CATEGORIES[(p - 1) % len(CATEGORIES)]
            base_demand = rng.uniform(40, 120)
            base_price = rng.uniform(10, 250)
            trend = rng.uniform(-0.03, 0.06)  # slow drift over time
            price_elasticity = rng.uniform(-1.5, -0.4)

            # seasonal + weekly signals
            weekly = 1 + 0.25 * np.sin(2 * np.pi * (day_index % 7) / 7)
            yearly = 1 + 0.30 * np.sin(2 * np.pi * day_index / 365.0)
            noise = rng.normal(1.0, 0.12, size=days)

            promo = rng.random(days) < 0.10          # 10% of days on promo
            holiday = rng.random(days) < 0.05         # 5% holidays
            discount = np.where(promo, rng.choice([5, 10, 15, 20, 25], size=days), 0)

            weather = rng.choice(WEATHER, size=days, p=[0.45, 0.25, 0.2, 0.1])
            weather_mult = np.select(
                [weather == "Sunny", weather == "Rainy", weather == "Cloudy", weather == "Snowy"],
                [1.05, 0.90, 1.0, 0.80], default=1.0,
            )

            price = base_price * (1 + rng.normal(0, 0.03, size=days))
            price = np.round(price * (1 - discount / 100.0), 2)
            competitor_price = np.round(base_price * (1 + rng.normal(0, 0.05, size=days)), 2)

            price_effect = (price / base_price) ** price_elasticity
            promo_boost = np.where(promo, 1.35, 1.0) * np.where(holiday, 1.25, 1.0)

            demand = (
                base_demand
                * store_level
                * (1 + trend * (day_index / 365.0))
                * weekly * yearly * weather_mult * price_effect * promo_boost * noise
            )
            units_sold = np.clip(np.round(demand), 0, None).astype(int)

            # Inventory holds a realistic spread of days-of-cover (~1 to 16 days of
            # demand), so the optimizer yields a healthy mix of stock statuses.
            days_of_cover = rng.uniform(1.0, 16.0, size=days)
            inventory = np.clip(
                np.round(demand * days_of_cover), 0, None
            ).astype(int)
            units_ordered = np.clip(
                np.round(units_sold * rng.uniform(0.8, 1.3, size=days)), 0, None
            ).astype(int)
            demand_forecast = np.round(units_sold * rng.uniform(0.9, 1.1, size=days), 2)

            df = pd.DataFrame({
                "Date": dates,
                "Store ID": store_id,
                "Product ID": product_id,
                "Category": category,
                "Region": region,
                "Inventory Level": inventory,
                "Units Sold": units_sold,
                "Units Ordered": units_ordered,
                "Demand Forecast": demand_forecast,
                "Price": price,
                "Discount": discount,
                "Weather Condition": weather,
                "Holiday/Promotion": holiday.astype(int),
                "Competitor Pricing": competitor_price,
                "Seasonality": [_season_for_month(m) for m in dates.month],
            })
            rows.append(df)

    data = pd.concat(rows, ignore_index=True)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic retail inventory data")
    parser.add_argument("--stores", type=int, default=5)
    parser.add_argument("--products", type=int, default=20)
    parser.add_argument("--days", type=int, default=730)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default=str(Path(__file__).parent / "retail_store_inventory.csv"))
    args = parser.parse_args()

    df = generate(args.stores, args.products, args.days, args.seed)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df):,} rows to {args.out}")
    print(f"Stores={args.stores}  Products={args.products}  Days={args.days}")
    print(df.head())


if __name__ == "__main__":
    main()

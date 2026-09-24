"""Pydantic request/response models for the API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class KPIs(BaseModel):
    total_skus: int
    healthy: int
    warning: int
    critical: int
    total_potential_lost_revenue: float
    avg_days_of_cover: float
    units_to_reorder: int


class FeatureImportance(BaseModel):
    feature: str
    importance: float


class Metrics(BaseModel):
    mae: float
    rmse: float
    mape: float
    r2: float
    train_rows: int
    test_rows: int
    n_features: int
    cutoff_date: str
    model: str
    kpis: KPIs
    feature_importance: list[FeatureImportance]


class InventoryItem(BaseModel):
    store_id: str = Field(alias="Store ID")
    product_id: str = Field(alias="Product ID")
    category: str = Field(alias="Category")
    date: str = Field(alias="Date")
    actual_sales: float = Field(alias="Actual_Sales")
    predicted_demand: float = Field(alias="Predicted_Demand")
    inventory_level: float = Field(alias="Inventory Level")
    price: float = Field(alias="Price")
    safety_stock: float = Field(alias="Safety_Stock")
    reorder_point: float = Field(alias="Reorder_Point")
    days_of_cover: float = Field(alias="Days_of_Cover")
    stock_status: str = Field(alias="Stock_Status")
    recommended_order_qty: int = Field(alias="Recommended_Order_Qty")
    potential_lost_revenue: float = Field(alias="Potential_Lost_Revenue")

    model_config = {"populate_by_name": True}


class SimulationRequest(BaseModel):
    """What-if inputs for a single-SKU forecast + optimization."""
    inventory_level: float = Field(..., ge=0, description="Current on-hand units")
    price: float = Field(..., gt=0, description="Selling price per unit")
    lag_7: float = Field(..., ge=0, description="Units sold 7 days ago")
    rolling_mean_7: float = Field(..., ge=0, description="Avg daily sales last 7 days")
    lead_time_days: int = Field(3, ge=1, le=30)
    discount: float = Field(0, ge=0, le=90)
    is_holiday_promo: bool = False
    category: str = "Groceries"
    region: str = "North"
    weather: str = "Sunny"
    season: str = "Summer"


class SimulationResponse(BaseModel):
    predicted_demand: float
    safety_stock: float
    reorder_point: float
    days_of_cover: float
    stock_status: str
    recommended_order_qty: int
    potential_lost_revenue: float

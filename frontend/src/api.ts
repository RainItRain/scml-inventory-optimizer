// Typed API client. All calls are same-origin relative (dev uses a Vite proxy;
// prod is served by FastAPI itself), so no base URL config is needed.

export interface KPIs {
  total_skus: number;
  healthy: number;
  warning: number;
  critical: number;
  total_potential_lost_revenue: number;
  avg_days_of_cover: number;
  units_to_reorder: number;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface Metrics {
  mae: number;
  rmse: number;
  mape: number;
  r2: number;
  train_rows: number;
  test_rows: number;
  n_features: number;
  cutoff_date: string;
  model: string;
  kpis: KPIs;
  feature_importance: FeatureImportance[];
}

export interface InventoryItem {
  "Store ID": string;
  "Product ID": string;
  Category: string;
  Date: string;
  Actual_Sales: number;
  Predicted_Demand: number;
  "Inventory Level": number;
  Price: number;
  Safety_Stock: number;
  Reorder_Point: number;
  Days_of_Cover: number;
  Stock_Status: "HEALTHY" | "WARNING" | "CRITICAL";
  Recommended_Order_Qty: number;
  Potential_Lost_Revenue: number;
}

export interface SimulationRequest {
  inventory_level: number;
  price: number;
  lag_7: number;
  rolling_mean_7: number;
  lead_time_days: number;
  discount: number;
  is_holiday_promo: boolean;
  category: string;
  region: string;
  weather: string;
  season: string;
}

export interface SimulationResponse {
  predicted_demand: number;
  safety_stock: number;
  reorder_point: number;
  days_of_cover: number;
  stock_status: "HEALTHY" | "WARNING" | "CRITICAL";
  recommended_order_qty: number;
  potential_lost_revenue: number;
}

async function getJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  metrics: () => getJSON<Metrics>("/api/metrics"),
  reorder: (limit = 15) =>
    getJSON<{ count: number; items: InventoryItem[] }>(
      `/api/reorder-recommendations?limit=${limit}`
    ),
  inventory: (params: Record<string, string | number> = {}) => {
    const q = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString();
    return getJSON<{ total: number; items: InventoryItem[] }>(
      `/api/inventory?${q}`
    );
  },
  filters: () =>
    getJSON<{ stores: string[]; categories: string[]; statuses: string[] }>(
      "/api/filters"
    ),
  simulate: async (body: SimulationRequest): Promise<SimulationResponse> => {
    const res = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  },
};

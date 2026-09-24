import { useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { api, type SimulationRequest, type SimulationResponse } from "../api";
import { STATUS_BADGE } from "../lib";

const DEFAULTS: SimulationRequest = {
  inventory_level: 120,
  price: 45,
  lag_7: 90,
  rolling_mean_7: 85,
  lead_time_days: 3,
  discount: 0,
  is_holiday_promo: false,
  category: "Groceries",
  region: "North",
  weather: "Sunny",
  season: "Summer",
};

const CATEGORIES = ["Groceries", "Electronics", "Clothing", "Toys", "Furniture"];
const REGIONS = ["North", "South", "East", "West"];
const WEATHER = ["Sunny", "Rainy", "Cloudy", "Snowy"];
const SEASONS = ["Spring", "Summer", "Autumn", "Winter"];

function NumField({
  label,
  value,
  onChange,
  step = 1,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  step?: number;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs text-slate-400">{label}</span>
      <input
        type="number"
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        className="rounded-lg bg-slate-900/70 ring-1 ring-slate-700/60 px-3 py-1.5 text-sm text-slate-100 focus:outline-none focus:ring-sky-500"
      />
    </label>
  );
}

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs text-slate-400">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg bg-slate-900/70 ring-1 ring-slate-700/60 px-3 py-1.5 text-sm text-slate-100 focus:outline-none focus:ring-sky-500"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function Simulator() {
  const [form, setForm] = useState<SimulationRequest>(DEFAULTS);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof SimulationRequest>(k: K, v: SimulationRequest[K]) =>
    setForm((f) => ({ ...f, [k]: v }));

  async function run() {
    setLoading(true);
    setError(null);
    try {
      setResult(await api.simulate(form));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-xl bg-slate-800/50 ring-1 ring-slate-700/60 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles size={18} className="text-violet-400" />
        <h3 className="text-sm font-semibold text-slate-200">
          What-If Simulator
        </h3>
        <span className="text-xs text-slate-400">
          live forecast + reorder decision for any SKU
        </span>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="grid grid-cols-2 gap-3">
          <NumField
            label="Inventory on hand"
            value={form.inventory_level}
            onChange={(v) => set("inventory_level", v)}
          />
          <NumField
            label="Unit price ($)"
            value={form.price}
            onChange={(v) => set("price", v)}
            step={0.5}
          />
          <NumField
            label="Sales 7 days ago"
            value={form.lag_7}
            onChange={(v) => set("lag_7", v)}
          />
          <NumField
            label="Avg daily sales (7d)"
            value={form.rolling_mean_7}
            onChange={(v) => set("rolling_mean_7", v)}
          />
          <NumField
            label="Lead time (days)"
            value={form.lead_time_days}
            onChange={(v) => set("lead_time_days", Math.max(1, v))}
          />
          <NumField
            label="Discount (%)"
            value={form.discount}
            onChange={(v) => set("discount", v)}
          />
          <SelectField
            label="Category"
            value={form.category}
            options={CATEGORIES}
            onChange={(v) => set("category", v)}
          />
          <SelectField
            label="Region"
            value={form.region}
            options={REGIONS}
            onChange={(v) => set("region", v)}
          />
          <SelectField
            label="Weather"
            value={form.weather}
            options={WEATHER}
            onChange={(v) => set("weather", v)}
          />
          <SelectField
            label="Season"
            value={form.season}
            options={SEASONS}
            onChange={(v) => set("season", v)}
          />
          <label className="col-span-2 flex items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={form.is_holiday_promo}
              onChange={(e) => set("is_holiday_promo", e.target.checked)}
              className="accent-violet-500"
            />
            Holiday / promotion active
          </label>
          <button
            onClick={run}
            disabled={loading}
            className="col-span-2 mt-1 inline-flex items-center justify-center gap-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-60 px-4 py-2 text-sm font-medium text-white transition"
          >
            {loading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Sparkles size={16} />
            )}
            Predict & Optimize
          </button>
        </div>

        <div className="rounded-lg bg-slate-900/50 ring-1 ring-slate-700/50 p-4 flex flex-col justify-center">
          {error && <p className="text-sm text-red-400">Error: {error}</p>}
          {!result && !error && (
            <p className="text-sm text-slate-500 text-center">
              Adjust the inputs and run a prediction to see the recommended
              action.
            </p>
          )}
          {result && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Recommendation</span>
                <span
                  className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${STATUS_BADGE[result.stock_status]}`}
                >
                  {result.stock_status}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Metric label="Predicted demand/day" value={result.predicted_demand} />
                <Metric label="Days of cover" value={`${result.days_of_cover}d`} />
                <Metric label="Reorder point" value={Math.round(result.reorder_point)} />
                <Metric label="Safety stock" value={Math.round(result.safety_stock)} />
                <Metric
                  label="Order now"
                  value={result.recommended_order_qty}
                  accent="text-violet-300"
                />
                <Metric
                  label="$ at risk"
                  value={`$${result.potential_lost_revenue.toLocaleString()}`}
                  accent="text-red-300"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  accent = "text-slate-100",
}: {
  label: string;
  value: string | number;
  accent?: string;
}) {
  return (
    <div className="rounded-lg bg-slate-800/60 ring-1 ring-slate-700/50 p-2.5">
      <div className="text-[11px] text-slate-400">{label}</div>
      <div className={`text-lg font-semibold ${accent}`}>{value}</div>
    </div>
  );
}

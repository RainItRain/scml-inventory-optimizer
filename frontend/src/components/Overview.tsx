import { TrendingUp, PackageCheck, Upload, Sparkles } from "lucide-react";

const CHIPS = [
  { icon: <TrendingUp size={13} />, label: "Demand forecasting" },
  { icon: <PackageCheck size={13} />, label: "Inventory optimization" },
  { icon: <Sparkles size={13} />, label: "What-if simulator" },
  { icon: <Upload size={13} />, label: "Bring your own data" },
];

export default function Overview() {
  return (
    <section className="rounded-xl bg-gradient-to-br from-sky-900/20 via-slate-800/50 to-violet-900/20 ring-1 ring-slate-700/60 p-5">
      <h2 className="text-lg font-semibold text-slate-100 mb-2">
        What is SupplyIQ?
      </h2>
      <p className="text-sm text-slate-300 leading-relaxed max-w-4xl">
        <strong className="text-slate-100">
          SupplyIQ is an end-to-end machine-learning platform that helps retailers
          forecast demand and make smarter inventory decisions.
        </strong>{" "}
        It learns from historical sales, pricing, promotions, weather, and
        seasonality to predict how many units each product will sell at each store —
        then turns those forecasts into action: calculating safety stock and reorder
        points, flagging stockout risks before they happen, and ranking which items
        to restock first by the revenue they put at risk. Explore the live model on
        sample data, run what-if scenarios for any SKU, or upload your own dataset to
        get a custom forecast accuracy (R²) and reorder plan in seconds.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {CHIPS.map((c) => (
          <span
            key={c.label}
            className="inline-flex items-center gap-1.5 rounded-full bg-slate-800/70 ring-1 ring-slate-700/60 px-3 py-1 text-xs text-slate-300"
          >
            <span className="text-sky-400">{c.icon}</span>
            {c.label}
          </span>
        ))}
      </div>
    </section>
  );
}

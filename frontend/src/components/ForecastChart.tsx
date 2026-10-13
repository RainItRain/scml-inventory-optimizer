import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { LineChart as LineIcon } from "lucide-react";
import { api, type ForecastPoint, type SeriesKey } from "../api";

export default function ForecastChart() {
  const [keys, setKeys] = useState<SeriesKey[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [series, setSeries] = useState<ForecastPoint[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.seriesKeys(40).then((r) => {
      setKeys(r.items);
      if (r.items.length) {
        setSelected(`${r.items[0].store_id}|${r.items[0].product_id}`);
      }
    });
  }, []);

  useEffect(() => {
    if (!selected) return;
    const [storeId, productId] = selected.split("|");
    setLoading(true);
    api
      .forecastSeries(storeId, productId)
      .then((r) => setSeries(r.series))
      .finally(() => setLoading(false));
  }, [selected]);

  return (
    <div className="rounded-xl bg-slate-800/50 ring-1 ring-slate-700/60 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <LineIcon size={18} className="text-sky-400" />
          <h3 className="text-sm font-semibold text-slate-200">
            Demand Forecast vs. Actual
          </h3>
        </div>
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="rounded-lg bg-slate-900/70 ring-1 ring-slate-700/60 px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:ring-sky-500"
        >
          {keys.map((k) => (
            <option key={`${k.store_id}|${k.product_id}`} value={`${k.store_id}|${k.product_id}`}>
              {k.store_id} · {k.product_id} ({k.points} days)
            </option>
          ))}
        </select>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={series} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="date"
            stroke="#64748b"
            fontSize={10}
            tickFormatter={(d) => String(d).slice(5)}
            minTickGap={30}
          />
          <YAxis stroke="#64748b" fontSize={11} />
          <Tooltip
            contentStyle={{
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: 8,
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual sales"
            stroke="#22c55e"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="predicted"
            name="Forecast"
            stroke="#38bdf8"
            strokeWidth={2}
            strokeDasharray="5 3"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
      {loading && (
        <p className="text-xs text-slate-500 text-center mt-1">loading series…</p>
      )}
    </div>
  );
}

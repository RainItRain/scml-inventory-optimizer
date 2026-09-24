import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import type { Metrics } from "../api";
import { STATUS_COLORS } from "../lib";

const Panel = ({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) => (
  <div className="rounded-xl bg-slate-800/50 ring-1 ring-slate-700/60 p-4">
    <h3 className="text-sm font-semibold text-slate-200 mb-3">{title}</h3>
    {children}
  </div>
);

export function StatusPie({ k }: { k: Metrics["kpis"] }) {
  const data = [
    { name: "Healthy", value: k.healthy },
    { name: "Warning", value: k.warning },
    { name: "Critical", value: k.critical },
  ];
  const colors = [STATUS_COLORS.HEALTHY, STATUS_COLORS.WARNING, STATUS_COLORS.CRITICAL];
  return (
    <Panel title="Inventory Health Distribution">
      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={55}
            outerRadius={90}
            paddingAngle={2}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={colors[i]} stroke="#0b1120" />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: 8,
              color: "#e2e8f0",
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </Panel>
  );
}

export function FeatureImportanceChart({ m }: { m: Metrics }) {
  const data = m.feature_importance.slice(0, 8).map((f) => ({
    feature: f.feature.length > 16 ? f.feature.slice(0, 15) + "…" : f.feature,
    importance: +(f.importance * 100).toFixed(1),
  }));
  return (
    <Panel title="What Drives the Forecast (Feature Importance %)">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} layout="vertical" margin={{ left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis type="number" stroke="#64748b" fontSize={11} />
          <YAxis
            type="category"
            dataKey="feature"
            stroke="#94a3b8"
            fontSize={11}
            width={95}
          />
          <Tooltip
            contentStyle={{
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: 8,
            }}
            cursor={{ fill: "#1e293b55" }}
          />
          <Bar dataKey="importance" fill="#38bdf8" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Panel>
  );
}

export function MetricsPanel({ m }: { m: Metrics }) {
  const items = [
    { label: "R² Score", value: m.r2.toFixed(3), hint: "variance explained" },
    { label: "MAPE", value: `${m.mape}%`, hint: "mean abs % error" },
    { label: "MAE", value: m.mae.toFixed(1), hint: "units off, avg" },
    { label: "RMSE", value: m.rmse.toFixed(1), hint: "penalizes big misses" },
  ];
  return (
    <Panel title="Model Performance (out-of-time test set)">
      <div className="grid grid-cols-2 gap-3">
        {items.map((it) => (
          <div
            key={it.label}
            className="rounded-lg bg-slate-900/60 ring-1 ring-slate-700/50 p-3"
          >
            <div className="text-xs text-slate-400">{it.label}</div>
            <div className="text-xl font-semibold text-sky-300">{it.value}</div>
            <div className="text-[10px] text-slate-500">{it.hint}</div>
          </div>
        ))}
      </div>
      <p className="mt-3 text-xs text-slate-400 leading-relaxed">
        {m.model} · trained on {m.train_rows.toLocaleString()} rows, validated on{" "}
        {m.test_rows.toLocaleString()} future rows (after {m.cutoff_date}).
      </p>
    </Panel>
  );
}

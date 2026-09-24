import {
  Boxes,
  AlertTriangle,
  DollarSign,
  PackagePlus,
  CalendarClock,
  ShieldCheck,
} from "lucide-react";
import type { KPIs } from "../api";
import { compact, money } from "../lib";

function Card({
  icon,
  label,
  value,
  sub,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  accent: string;
}) {
  return (
    <div className="rounded-xl bg-slate-800/50 ring-1 ring-slate-700/60 p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
          {label}
        </span>
        <span className={`${accent}`}>{icon}</span>
      </div>
      <div className="text-2xl font-semibold text-slate-100">{value}</div>
      {sub && <div className="text-xs text-slate-400">{sub}</div>}
    </div>
  );
}

export default function Kpis({ k }: { k: KPIs }) {
  const attention = k.warning + k.critical;
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
      <Card
        icon={<Boxes size={18} />}
        label="SKUs Tracked"
        value={compact(k.total_skus)}
        sub="store × product × day"
        accent="text-sky-400"
      />
      <Card
        icon={<ShieldCheck size={18} />}
        label="Healthy Stock"
        value={compact(k.healthy)}
        sub={`${((k.healthy / k.total_skus) * 100).toFixed(0)}% of inventory`}
        accent="text-green-400"
      />
      <Card
        icon={<AlertTriangle size={18} />}
        label="Need Attention"
        value={compact(attention)}
        sub={`${compact(k.critical)} critical`}
        accent="text-amber-400"
      />
      <Card
        icon={<DollarSign size={18} />}
        label="Lost Revenue at Risk"
        value={money(k.total_potential_lost_revenue)}
        sub="if unaddressed"
        accent="text-red-400"
      />
      <Card
        icon={<PackagePlus size={18} />}
        label="Units to Reorder"
        value={compact(k.units_to_reorder)}
        sub="recommended"
        accent="text-violet-400"
      />
      <Card
        icon={<CalendarClock size={18} />}
        label="Avg Days of Cover"
        value={`${k.avg_days_of_cover}d`}
        sub="inventory runway"
        accent="text-teal-400"
      />
    </div>
  );
}

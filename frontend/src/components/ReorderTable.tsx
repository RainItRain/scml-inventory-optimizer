import { Download } from "lucide-react";
import type { InventoryItem } from "../api";
import { STATUS_BADGE } from "../lib";

function exportCsv(items: InventoryItem[]) {
  if (!items.length) return;
  const cols = Object.keys(items[0]);
  const esc = (v: unknown) => {
    const s = String(v ?? "");
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const csv = [
    cols.join(","),
    ...items.map((row) =>
      cols.map((c) => esc((row as unknown as Record<string, unknown>)[c])).join(",")
    ),
  ].join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = "reorder_recommendations.csv";
  a.click();
  URL.revokeObjectURL(url);
}

function Badge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ${STATUS_BADGE[status]}`}
    >
      {status}
    </span>
  );
}

export default function ReorderTable({ items }: { items: InventoryItem[] }) {
  return (
    <div className="rounded-xl bg-slate-800/50 ring-1 ring-slate-700/60 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-200">
          Priority Reorder Recommendations
        </h3>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">ranked by revenue at risk</span>
          <button
            onClick={() => exportCsv(items)}
            disabled={!items.length}
            className="inline-flex items-center gap-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 disabled:opacity-50 px-2.5 py-1 text-xs font-medium text-slate-100 transition"
          >
            <Download size={13} /> Export CSV
          </button>
        </div>
      </div>
      <div className="overflow-x-auto scroll-thin">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-700/60">
              <th className="py-2 pr-3">Store</th>
              <th className="py-2 pr-3">Product</th>
              <th className="py-2 pr-3">Category</th>
              <th className="py-2 pr-3 text-right">Forecast</th>
              <th className="py-2 pr-3 text-right">On Hand</th>
              <th className="py-2 pr-3 text-right">Reorder Pt</th>
              <th className="py-2 pr-3 text-right">Order Qty</th>
              <th className="py-2 pr-3">Status</th>
              <th className="py-2 pr-3 text-right">$ at Risk</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it, i) => (
              <tr
                key={i}
                className="border-b border-slate-800/60 hover:bg-slate-700/20"
              >
                <td className="py-2 pr-3 font-mono text-slate-300">
                  {it["Store ID"]}
                </td>
                <td className="py-2 pr-3 font-mono text-slate-300">
                  {it["Product ID"]}
                </td>
                <td className="py-2 pr-3 text-slate-400">{it.Category}</td>
                <td className="py-2 pr-3 text-right">{it.Predicted_Demand}</td>
                <td className="py-2 pr-3 text-right">{it["Inventory Level"]}</td>
                <td className="py-2 pr-3 text-right">
                  {Math.round(it.Reorder_Point)}
                </td>
                <td className="py-2 pr-3 text-right font-semibold text-violet-300">
                  {it.Recommended_Order_Qty}
                </td>
                <td className="py-2 pr-3">
                  <Badge status={it.Stock_Status} />
                </td>
                <td className="py-2 pr-3 text-right font-semibold text-red-300">
                  ${it.Potential_Lost_Revenue.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

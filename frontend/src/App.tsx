import { useEffect, useState } from "react";
import { Activity, Github, TrendingUp } from "lucide-react";
import { api, type InventoryItem, type Metrics } from "./api";
import Kpis from "./components/Kpis";
import { StatusPie, FeatureImportanceChart, MetricsPanel } from "./components/Charts";
import ReorderTable from "./components/ReorderTable";
import Simulator from "./components/Simulator";

const GITHUB_URL = "https://github.com/amanibharne/scml-inventory-optimizer";

export default function App() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [reorder, setReorder] = useState<InventoryItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.metrics(), api.reorder(12)])
      .then(([m, r]) => {
        setMetrics(m);
        setReorder(r.items);
      })
      .catch((e) => setError((e as Error).message));
  }, []);

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800/80 bg-slate-900/40 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="grid place-items-center h-9 w-9 rounded-lg bg-gradient-to-br from-sky-500 to-violet-600">
              <TrendingUp size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-base font-semibold text-slate-100 leading-tight">
                SupplyIQ
              </h1>
              <p className="text-xs text-slate-400 leading-tight">
                AI Inventory &amp; Demand Optimization
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {metrics && (
              <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-green-500/10 px-3 py-1 text-xs font-medium text-green-400 ring-1 ring-green-500/30">
                <Activity size={13} /> Model live · R² {metrics.r2.toFixed(3)}
              </span>
            )}
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 ring-1 ring-slate-700 transition"
            >
              <Github size={14} /> Source
            </a>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {error && (
          <div className="rounded-xl bg-red-500/10 ring-1 ring-red-500/30 p-4 text-sm text-red-300">
            Could not reach the API ({error}). Make sure the backend is running
            (<code className="text-red-200">uvicorn app.main:app</code>) and the
            model is trained (<code className="text-red-200">python ml/train.py</code>).
          </div>
        )}

        {!metrics && !error && (
          <div className="grid place-items-center py-20 text-slate-400">
            <Activity className="animate-pulse mb-2" /> Loading model insights…
          </div>
        )}

        {metrics && (
          <>
            <section>
              <h2 className="text-sm font-semibold text-slate-300 mb-3">
                Supply Chain Health Overview
              </h2>
              <Kpis k={metrics.kpis} />
            </section>

            <section className="grid lg:grid-cols-3 gap-4">
              <StatusPie k={metrics.kpis} />
              <FeatureImportanceChart m={metrics} />
              <MetricsPanel m={metrics} />
            </section>

            <section>
              <Simulator />
            </section>

            <section>
              <ReorderTable items={reorder} />
            </section>
          </>
        )}

        <footer className="pt-4 pb-8 text-center text-xs text-slate-500">
          Built with FastAPI · scikit-learn · React · Recharts ·{" "}
          <a href={GITHUB_URL} className="underline hover:text-slate-300">
            source on GitHub
          </a>
        </footer>
      </main>
    </div>
  );
}

import { useRef, useState } from "react";
import { Upload, Download, Loader2, FileCheck2, AlertCircle } from "lucide-react";
import { api, type AnalyzeResult } from "../api";
import Kpis from "./Kpis";
import { StatusPie, FeatureImportanceChart, MetricsPanel } from "./Charts";
import ReorderTable from "./ReorderTable";

export default function DataUpload() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResult | null>(null);

  async function handleFile(file: File) {
    setFileName(file.name);
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      setResult(await api.analyze(file));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-xl bg-slate-800/50 ring-1 ring-slate-700/60 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
        <h3 className="text-sm font-semibold text-slate-200">
          Analyze Your Own Data
        </h3>
        <a
          href={api.sampleTemplateUrl}
          className="inline-flex items-center gap-1.5 text-xs text-sky-400 hover:text-sky-300"
        >
          <Download size={13} /> Download sample template
        </a>
      </div>
      <p className="text-xs text-slate-400 mb-3">
        Upload a retail inventory CSV and the platform will train a fresh
        forecasting model on <em>your</em> data and run the full optimization —
        your own R², demand drivers, and reorder plan. Needs the same columns as
        the template (Date, Store ID, Product ID, Category, Region, Inventory
        Level, Units Sold, Price, Weather Condition, Seasonality).
      </p>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const f = e.dataTransfer.files?.[0];
          if (f) handleFile(f);
        }}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-6 text-center transition ${
          dragging
            ? "border-sky-500 bg-sky-500/5"
            : "border-slate-700 hover:border-slate-600 bg-slate-900/40"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />
        {loading ? (
          <div className="flex flex-col items-center gap-2 text-slate-300">
            <Loader2 className="animate-spin" />
            <span className="text-sm">Training a model on your data…</span>
            <span className="text-xs text-slate-500">
              feature engineering → forecast → optimization
            </span>
          </div>
        ) : fileName && !error ? (
          <div className="flex flex-col items-center gap-1 text-slate-300">
            <FileCheck2 className="text-green-400" />
            <span className="text-sm">{fileName}</span>
            <span className="text-xs text-slate-500">
              Click to analyze a different file
            </span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-1 text-slate-400">
            <Upload />
            <span className="text-sm">
              Drop a CSV here or <span className="text-sky-400">browse</span>
            </span>
            <span className="text-xs text-slate-500">max 25 MB</span>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 flex items-start gap-2 rounded-lg bg-red-500/10 ring-1 ring-red-500/30 p-3 text-sm text-red-300">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="mt-5 space-y-4">
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <FileCheck2 size={16} className="text-green-400" />
            Results for <span className="font-mono text-slate-200">{fileName}</span>
          </div>
          <Kpis k={result.kpis} />
          <div className="grid lg:grid-cols-3 gap-4">
            <StatusPie k={result.kpis} />
            <FeatureImportanceChart m={result} />
            <MetricsPanel m={result} />
          </div>
          {result.recommendations.length > 0 && (
            <ReorderTable items={result.recommendations} />
          )}
        </div>
      )}
    </div>
  );
}

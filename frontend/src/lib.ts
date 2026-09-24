export const STATUS_COLORS: Record<string, string> = {
  HEALTHY: "#22c55e",
  WARNING: "#f59e0b",
  CRITICAL: "#ef4444",
};

export const STATUS_BADGE: Record<string, string> = {
  HEALTHY: "bg-green-500/15 text-green-400 ring-green-500/30",
  WARNING: "bg-amber-500/15 text-amber-400 ring-amber-500/30",
  CRITICAL: "bg-red-500/15 text-red-400 ring-red-500/30",
};

export function money(n: number): string {
  if (Math.abs(n) >= 1_000_000)
    return `$${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}

export function compact(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

"""
Natural-language "AI insights" for a dashboard snapshot.

If ANTHROPIC_API_KEY is set, a concise operations briefing is written by Claude
(model configurable via INSIGHT_MODEL, default claude-opus-5-5). Otherwise — and
on any error — it falls back to a deterministic, well-written rule-based summary,
so the feature always returns something useful (and the live demo needs no key).
"""
from __future__ import annotations

import os
from typing import Any

SYSTEM_PROMPT = (
    "You are a supply-chain operations analyst. Given summary statistics from a "
    "demand-forecasting and inventory-optimization model, write a crisp briefing "
    "for a warehouse/operations manager. Be specific and quantitative, plain and "
    "non-technical. 3-5 sentences or short bullets. No preamble, no restating the "
    "numbers mechanically — interpret them and say what to do next."
)


def generate_insight(data: dict[str, Any]) -> dict[str, str]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return {"insight": _claude_summary(data, api_key), "source": "claude"}
        except Exception as exc:  # pragma: no cover - network/SDK/runtime guard
            print(f"[insights] Claude unavailable, using rule-based fallback: {exc}")
    return {"insight": _rule_based_summary(data), "source": "rule-based"}


def _claude_summary(data: dict[str, Any], api_key: str) -> str:
    from anthropic import Anthropic  # lazy import so the app runs without the SDK

    client = Anthropic(api_key=api_key)
    model = os.getenv("INSIGHT_MODEL", "claude-opus-5-5")
    msg = client.messages.create(
        model=model,
        max_tokens=700,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_prompt(data)}],
    )
    if getattr(msg, "stop_reason", None) == "refusal":
        raise RuntimeError("model refused")
    text = "".join(
        getattr(b, "text", "") for b in msg.content if getattr(b, "type", None) == "text"
    ).strip()
    if not text:
        raise RuntimeError("empty response")
    return text


def _build_prompt(data: dict[str, Any]) -> str:
    k = data.get("kpis", {})
    feats = ", ".join(f["feature"] for f in data.get("feature_importance", [])[:5]) or "n/a"
    recs = data.get("recommendations", [])[:5]
    rec_lines = "\n".join(
        f"- {r.get('Store ID')}/{r.get('Product ID')} ({r.get('Category')}): "
        f"forecast {r.get('Predicted_Demand')}/day, on-hand {r.get('Inventory Level')}, "
        f"reorder {r.get('Recommended_Order_Qty')} units, "
        f"${r.get('Potential_Lost_Revenue')} at risk"
        for r in recs
    ) or "- none"
    return (
        f"Dataset: {data.get('label', 'the dataset')}\n"
        f"Model: R²={data.get('r2')}, MAPE={data.get('mape')}%\n"
        f"SKUs tracked: {k.get('total_skus')}\n"
        f"Healthy: {k.get('healthy')}, Warning: {k.get('warning')}, "
        f"Critical: {k.get('critical')}\n"
        f"Revenue at risk: ${k.get('total_potential_lost_revenue')}\n"
        f"Units to reorder: {k.get('units_to_reorder')}\n"
        f"Avg days of cover: {k.get('avg_days_of_cover')}\n"
        f"Top demand drivers: {feats}\n"
        f"Highest-priority items:\n{rec_lines}\n"
    )


def _rule_based_summary(data: dict[str, Any]) -> str:
    k = data.get("kpis", {})
    total = max(int(k.get("total_skus", 0)), 1)
    healthy = int(k.get("healthy", 0))
    warning = int(k.get("warning", 0))
    critical = int(k.get("critical", 0))
    lost = float(k.get("total_potential_lost_revenue", 0))
    units = int(k.get("units_to_reorder", 0))
    cover = k.get("avg_days_of_cover", 0)
    r2 = data.get("r2", 0)
    mape = data.get("mape", 0)

    feats = [f["feature"] for f in data.get("feature_importance", [])[:3]]
    feats_txt = ", ".join(feats) if feats else "recent sales history"

    recs = data.get("recommendations", [])
    top = recs[0] if recs else None

    parts = [
        f"The demand model explains {r2:.0%} of sales variability "
        f"(R²={r2}) with an average error of about {mape:.0f}%, so its forecasts "
        f"are reliable enough to drive restocking decisions.",
        f"Of {total:,} tracked store-product combinations, "
        f"{healthy:,} ({healthy / total:.0%}) are healthy, {warning:,} need watching, "
        f"and {critical:,} are at critical stockout risk.",
        f"Acting on these protects roughly ${lost:,.0f} of at-risk revenue; the plan "
        f"recommends reordering about {units:,} units, with an average of "
        f"{cover} days of inventory cover across the catalogue.",
    ]
    if top:
        parts.append(
            f"Start with {top.get('Store ID')}/{top.get('Product ID')} "
            f"({top.get('Category')}): order ~{top.get('Recommended_Order_Qty')} units to "
            f"avoid ${top.get('Potential_Lost_Revenue'):,.0f} in lost sales."
        )
    parts.append(f"Demand is driven most by {feats_txt}.")
    return " ".join(parts)

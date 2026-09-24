# SupplyIQ — AI Inventory & Demand Optimization Platform

An end-to-end machine-learning system that **forecasts retail demand** and turns those
forecasts into **actionable inventory decisions** — safety stock, reorder points,
stockout risk, and revenue-prioritized reorder recommendations — served through a
FastAPI backend and an interactive React dashboard.

> Demand forecasting → inventory optimization → an operations dashboard a warehouse
> manager could actually use.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8-F7931E?logo=scikitlearn&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?logo=typescript&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

🔗 **Live demo:** _add your deployed URL here after following [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)_

---

## Features

- **Demand forecasting** with a `RandomForestRegressor` using leakage-free
  time-series features (7/14-day lags, rolling mean/std, calendar signals,
  encoded store/product/category/region/weather/season).
- **Out-of-time validation** — chronological train/test split (train on the past,
  test on the future) instead of a naive random split, so metrics reflect real
  forecasting performance: **R² ≈ 0.86, MAPE ≈ 12%**.
- **Inventory optimization** using textbook supply-chain formulas:
  - Safety stock = `Z · σ_demand · √lead_time` (Z = 1.65 → ~95% service level)
  - Reorder point = `avg_daily_demand · lead_time + safety_stock`
  - Stock status (HEALTHY / WARNING / CRITICAL), days of cover, recommended order qty
  - Potential lost revenue, used to **prioritize** which SKUs to reorder first.
- **Interactive dashboard**: KPI cards, inventory-health distribution, feature
  importance, model performance, a priority reorder table, and a **what-if
  simulator** that runs a live forecast + reorder decision for any SKU.
- **Reproducible** — a synthetic dataset generator recreates the schema of the
  Kaggle *Retail Store Inventory Forecasting* dataset, so the whole project runs
  end-to-end with zero external downloads.
- **Deployable** — single Docker container (FastAPI serves the compiled frontend),
  plus CI and one-click Render / Hugging Face Spaces configs.

## Architecture

```
                     ┌──────────────────────────────────────┐
   retail data ──►   │  ml/  feature engineering + training  │
 (or generated)      │  RandomForest → model.pkl + metrics   │
                     └───────────────┬──────────────────────┘
                                     │ artifacts (joblib/json)
                     ┌───────────────▼──────────────────────┐
   HTTP  ◄────────►  │  backend/  FastAPI  (/api/*)          │
                     │  forecasting + optimization endpoints │
                     └───────────────┬──────────────────────┘
                                     │ serves /
                     ┌───────────────▼──────────────────────┐
   browser  ◄──────► │  frontend/  React + Vite + Tailwind   │
                     │  Recharts dashboard + what-if sim     │
                     └──────────────────────────────────────┘
```

## Tech stack

| Layer     | Technologies |
|-----------|--------------|
| ML        | Python, scikit-learn, pandas, NumPy, joblib |
| Backend   | FastAPI, Pydantic, Uvicorn |
| Frontend  | React 18, TypeScript, Vite, Tailwind CSS v4, Recharts, lucide-react |
| DevOps    | Docker (multi-stage), GitHub Actions CI, Render / Hugging Face Spaces |

## Quickstart (local)

**Prerequisites:** Python 3.10+, Node 18+.

```bash
# 1. Train the model (auto-generates the dataset on first run)
pip install -r backend/requirements.txt
python ml/train.py

# 2. Backend API  →  http://localhost:8000
cd backend && uvicorn app.main:app --reload --port 8000

# 3. Frontend dev server  →  http://localhost:5173  (in a second terminal)
cd frontend && npm install && npm run dev
```

For a production-style single server, build the frontend first
(`cd frontend && npm run build`) and then just run the backend — FastAPI serves the
compiled app at `http://localhost:8000`.

### With Docker

```bash
docker build -t scml-optimizer .
docker run --rm -p 8000:7860 -e PORT=7860 scml-optimizer   # http://localhost:8000
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/health` | Service + artifact status |
| GET  | `/api/metrics` | Model metrics, KPIs, feature importance |
| GET  | `/api/inventory` | Inventory rows (filter by status/store/category) |
| GET  | `/api/reorder-recommendations` | Top SKUs to reorder, ranked by revenue at risk |
| GET  | `/api/filters` | Available stores / categories / statuses |
| POST | `/api/simulate` | Live forecast + reorder decision for a single SKU |

Interactive API docs are available at `/docs` (Swagger UI).

## Project structure

```
scml-inventory-optimizer/
├── data/generate_dataset.py   # synthetic dataset generator
├── ml/
│   ├── features.py            # leakage-free feature engineering
│   ├── optimize.py            # safety stock / reorder / status / lost revenue
│   ├── train.py               # pipeline → model + metrics + snapshot
│   └── artifacts/             # trained model, encoders, metrics, snapshot
├── backend/app/               # FastAPI app (main.py, schemas.py)
├── frontend/                  # React + TS + Tailwind + Recharts dashboard
├── Dockerfile                 # single-container build (frontend + API)
├── render.yaml                # Render blueprint
└── .github/workflows/ci.yml   # CI: train smoke test + frontend build
```

## Deployment

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for step-by-step Render and
Hugging Face Spaces instructions (both free).

## License

MIT — see [LICENSE](LICENSE).

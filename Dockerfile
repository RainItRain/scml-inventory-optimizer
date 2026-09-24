# ---------- Stage 1: build the React frontend ----------
FROM node:20-alpine AS frontend
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- Stage 2: Python API that also serves the frontend ----------
FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Backend dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Application code + trained ML artifacts (committed to the repo)
COPY ml/ ./ml/
COPY backend/ ./backend/
COPY data/ ./data/

# Compiled frontend from stage 1 -> served by FastAPI at "/"
COPY --from=frontend /web/dist ./frontend/dist

# If artifacts are missing for any reason, train at build time as a fallback.
RUN test -f ml/artifacts/model.pkl || python ml/train.py

WORKDIR /app/backend
EXPOSE 7860
# $PORT is provided by Render / Hugging Face Spaces; default 7860 for HF.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]

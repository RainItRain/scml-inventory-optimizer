.PHONY: help data train backend frontend dev build docker run clean

help:
	@echo "make data      - generate synthetic dataset"
	@echo "make train     - train model + build artifacts"
	@echo "make backend   - run FastAPI (http://localhost:8000)"
	@echo "make frontend  - run Vite dev server (http://localhost:5173)"
	@echo "make build     - build the frontend for production"
	@echo "make docker    - build the single-container image"
	@echo "make run       - run the container on http://localhost:8000"

data:
	python data/generate_dataset.py

train:
	python ml/train.py

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

build:
	cd frontend && npm ci && npm run build

docker:
	docker build -t scml-optimizer .

run:
	docker run --rm -p 8000:7860 -e PORT=7860 scml-optimizer

clean:
	rm -rf frontend/dist frontend/node_modules ml/artifacts/*.pkl data/*.csv

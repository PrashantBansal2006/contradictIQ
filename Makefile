# ContradictIQ — Makefile
# Primary targets: dev, test, seed, eval, smoke, lint

PYTHON   = backend/venv/Scripts/python
UVICORN  = backend/venv/Scripts/uvicorn
PYTEST   = backend/venv/Scripts/pytest
PIP      = backend/venv/Scripts/pip

.PHONY: dev backend frontend install test seed smoke eval lint clean

## ── Development ─────────────────────────────────────────────────────────────

dev:
	@echo "Starting backend + frontend..."
	start cmd /k "cd backend && ../$(UVICORN) app.main:app --reload --port 8000"
	start cmd /k "cd frontend && npm run dev"

backend:
	cd backend && ../$(UVICORN) app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

## ── Install ──────────────────────────────────────────────────────────────────

install:
	$(PIP) install -r backend/requirements.txt

## ── Test ─────────────────────────────────────────────────────────────────────

test:
	$(PYTEST) backend/tests -q --tb=short

test-core:
	$(PYTEST) backend/tests/core -q --tb=short --cov=backend/app/core --cov-report=term-missing

## ── Seed ─────────────────────────────────────────────────────────────────────

seed:
	$(PYTHON) backend/scripts/generate_demo_data.py

## ── Smoke ────────────────────────────────────────────────────────────────────

smoke:
	$(PYTHON) backend/scripts/smoke.py

## ── Eval ─────────────────────────────────────────────────────────────────────

eval:
	$(PYTHON) backend/app/eval/run_eval.py

## ── Lint ─────────────────────────────────────────────────────────────────────

lint:
	backend/venv/Scripts/ruff check backend/app
	backend/venv/Scripts/mypy backend/app --ignore-missing-imports

## ── Clean ────────────────────────────────────────────────────────────────────

clean:
	if exist data\app.db del /f data\app.db
	if exist data\uploads rmdir /s /q data\uploads
	$(PYTEST) --cache-clear -q || true

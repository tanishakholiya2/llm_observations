# LLM Observatory

LLM Observatory is an observability platform for request-level LLM telemetry. It measures latency, token usage, estimated cost, request volume, and errors, then exposes those signals through a FastAPI API and a React dashboard.

## Architecture

```text
React + Vite + Recharts  ->  FastAPI  ->  SQLAlchemy  ->  PostgreSQL
				 |                     |
		 Playground          BackgroundTasks
															 |
										configured LLM provider
										or deterministic local adapter
```

- `backend/app/main.py` owns the HTTP contract and background telemetry scheduling.
- `backend/app/provider.py` is the provider integration boundary. It accepts an OpenAI-compatible endpoint through environment variables and has a local fallback for development.
- `backend/app/models.py` is the SQLAlchemy representation of the single request-level table.
- `backend/app/metrics.py` keeps percentile calculation explicit and testable.
- `frontend/src/App.tsx` contains the dashboard, charts, request table/detail drawer, and playground.
- `db/schema.sql` makes the PostgreSQL table and required indexes visible without a migration framework.

## Run with Docker

Requirements: Docker Desktop.

```bash
cp .env.example .env
# Add LLM_API_URL and LLM_API_KEY only when using a real provider.
docker compose up --build
```

Open `http://localhost:5173`. The API is available at `http://localhost:8000` and its OpenAPI docs are at `http://localhost:8000/docs`.

## Run locally

Requirements: Python 3.12, Node.js 20+, npm, and PostgreSQL.

```bash
docker compose up -d postgres
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
export DATABASE_URL=postgresql+psycopg://observability:observability@localhost:5432/llm_observatory
uvicorn app.main:app --app-dir backend --reload
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

## API

- `POST /api/chat` accepts `prompt`, `model`, `temperature`, and optional `max_tokens`; returns the completion and request telemetry.
- `GET /api/metrics/overview` returns total requests, error rate, average latency, p50/p95/p99 latency, total tokens, and estimated cost.
- `GET /api/metrics/latency` returns hourly p50/p95/p99 latency points.
- `GET /api/metrics/tokens` returns hourly prompt/completion token points.
- `GET /api/requests` supports `page`, `page_size`, `model`, `status`, `start`, and `end`.

Example:

```bash
curl -X POST http://localhost:8000/api/chat \
	-H 'Content-Type: application/json' \
	-d '{"prompt":"Explain Kubernetes autoscaling","model":"your-model","temperature":0.7}'
```

## Technology choices and decisions

- FastAPI and Pydantic provide a concise typed HTTP boundary and automatic OpenAPI documentation.
- SQLAlchemy keeps persistence independent from route code and supports PostgreSQL in production plus SQLite-backed tests.
- React, Vite, and Recharts provide a lightweight client with direct control over the dashboard layout.
- Docker Compose makes the three runtime dependencies reproducible without adding a deployment platform abstraction.
- FastAPI `BackgroundTasks` keeps the request response path short while remaining understandable; a durable queue is the next scale step.

## Testing

```bash
cd backend
pytest -q
```

Tests cover percentile interpolation, token estimation, cost calculation, and API response contracts. Provider calls are isolated behind `provider.complete`, so provider-specific tests can be added without coupling them to the database.

## Scaling to 1M requests/day

One million requests per day is about 11.6 requests per second on average, but capacity should be sized for burst traffic. The next steps would be:

1. Put the API behind a load balancer and run multiple stateless FastAPI workers.
2. Replace in-process `BackgroundTasks` with a durable queue such as SQS, Redis Streams, or Kafka so telemetry is not lost when a worker exits.
3. Batch telemetry inserts and partition `llm_requests` by day or month; retain the timestamp/model/status indexes on each partition.
4. Add a read replica for dashboard aggregations, with short-lived cached metric responses.
5. Add sampling/redaction controls for prompt and response bodies, since text storage grows faster than numeric telemetry.
6. Add provider timeouts, retries with backoff, circuit breakers, rate limits, and metrics for the observability pipeline itself.

import time
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import Base, SessionLocal, engine, get_db
from .metrics import bucket_hour, hours_between, percentile
from .models import LlmRequest
from .provider import complete
from .schemas import ChatRequest, ChatResponse, LatencyPoint, OverviewResponse, PaginatedRequests, RequestResponse, TokenPoint
from .telemetry import persist_telemetry

settings = get_settings()
app = FastAPI(title="LLM Observatory", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def queue_telemetry(payload: dict) -> None:
    with SessionLocal() as db:
        persist_telemetry(db, **payload)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, background_tasks: BackgroundTasks) -> ChatResponse:
    request_id = uuid4()
    timestamp = datetime.now(timezone.utc)
    model = body.model or settings.llm_default_model
    started = time.perf_counter()
    try:
        completion = await complete(body.prompt, model, body.temperature, body.max_tokens)
        latency_ms = round((time.perf_counter() - started) * 1000)
        background_tasks.add_task(queue_telemetry, {"request_id": request_id, "timestamp": timestamp, "model": model, "prompt": body.prompt, "response": completion.response, "status": "success", "error_type": None, "latency_ms": latency_ms, "prompt_tokens": completion.prompt_tokens, "completion_tokens": completion.completion_tokens, "estimated_cost": completion.estimated_cost, "temperature": body.temperature, "max_tokens": body.max_tokens})
        return ChatResponse(response=completion.response, request_id=request_id, latency_ms=latency_ms, prompt_tokens=completion.prompt_tokens, completion_tokens=completion.completion_tokens, total_tokens=completion.prompt_tokens + completion.completion_tokens, estimated_cost=completion.estimated_cost)
    except Exception as error:
        latency_ms = round((time.perf_counter() - started) * 1000)
        background_tasks.add_task(queue_telemetry, {"request_id": request_id, "timestamp": timestamp, "model": model, "prompt": body.prompt, "response": None, "status": "error", "error_type": type(error).__name__, "latency_ms": latency_ms, "prompt_tokens": 0, "completion_tokens": 0, "estimated_cost": 0, "temperature": body.temperature, "max_tokens": body.max_tokens})
        raise HTTPException(status_code=502, detail="LLM provider request failed") from error


@app.get("/api/metrics/overview", response_model=OverviewResponse)
def metrics_overview(db: Session = Depends(get_db)) -> OverviewResponse:
    rows = list(db.scalars(select(LlmRequest)))
    latencies = [row.latency_ms for row in rows]
    errors = sum(row.status == "error" for row in rows)
    return OverviewResponse(total_requests=len(rows), error_rate=errors / len(rows) if rows else 0, avg_latency_ms=sum(latencies) / len(latencies) if latencies else 0, p50_latency_ms=percentile(latencies, .5), p95_latency_ms=percentile(latencies, .95), p99_latency_ms=percentile(latencies, .99), total_tokens=sum(row.total_tokens for row in rows), estimated_cost=float(sum(row.estimated_cost for row in rows)))


def time_window(rows: list[LlmRequest]) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    return (min((row.timestamp for row in rows), default=now), max((row.timestamp for row in rows), default=now))


@app.get("/api/metrics/latency", response_model=list[LatencyPoint])
def metrics_latency(db: Session = Depends(get_db)) -> list[LatencyPoint]:
    rows = list(db.scalars(select(LlmRequest).order_by(LlmRequest.timestamp)))
    start, end = time_window(rows)
    return [LatencyPoint(timestamp=hour, p50=percentile([r.latency_ms for r in rows if bucket_hour(r.timestamp) == hour], .5), p95=percentile([r.latency_ms for r in rows if bucket_hour(r.timestamp) == hour], .95), p99=percentile([r.latency_ms for r in rows if bucket_hour(r.timestamp) == hour], .99)) for hour in hours_between(start, end) if any(bucket_hour(r.timestamp) == hour for r in rows)]


@app.get("/api/metrics/tokens", response_model=list[TokenPoint])
def metrics_tokens(db: Session = Depends(get_db)) -> list[TokenPoint]:
    rows = list(db.scalars(select(LlmRequest).order_by(LlmRequest.timestamp)))
    start, end = time_window(rows)
    return [TokenPoint(timestamp=hour, prompt_tokens=sum(r.prompt_tokens for r in rows if bucket_hour(r.timestamp) == hour), completion_tokens=sum(r.completion_tokens for r in rows if bucket_hour(r.timestamp) == hour)) for hour in hours_between(start, end) if any(bucket_hour(r.timestamp) == hour for r in rows)]


@app.get("/api/requests", response_model=PaginatedRequests)
def requests(db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), model: str | None = None, request_status: str | None = Query(None, alias="status"), start: datetime | None = None, end: datetime | None = None) -> PaginatedRequests:
    statement = select(LlmRequest).order_by(LlmRequest.timestamp.desc())
    if model:
        statement = statement.where(LlmRequest.model == model)
    if request_status:
        statement = statement.where(LlmRequest.status == request_status)
    if start:
        statement = statement.where(LlmRequest.timestamp >= start)
    if end:
        statement = statement.where(LlmRequest.timestamp <= end)
    rows = list(db.scalars(statement))
    total = len(rows)
    items = rows[(page - 1) * page_size: page * page_size]
    return PaginatedRequests(items=[RequestResponse.model_validate(row) for row in items], total=total, page=page, page_size=page_size)

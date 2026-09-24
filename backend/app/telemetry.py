from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from .models import LlmRequest


def persist_telemetry(
    db: Session,
    *,
    request_id: UUID,
    timestamp: datetime,
    model: str,
    prompt: str,
    response: str | None,
    status: str,
    error_type: str | None,
    latency_ms: int,
    prompt_tokens: int,
    completion_tokens: int,
    estimated_cost: float,
    temperature: float | None,
    max_tokens: int | None,
) -> None:
    db.add(LlmRequest(
        id=request_id,
        timestamp=timestamp,
        model=model,
        prompt=prompt,
        response=response,
        status=status,
        error_type=error_type,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        estimated_cost=estimated_cost,
        temperature=temperature,
        max_tokens=max_tokens,
        created_at=datetime.now(timezone.utc),
    ))
    db.commit()

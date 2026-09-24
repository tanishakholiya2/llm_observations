from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1)
    model: str | None = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int | None = Field(default=None, gt=0)


class ChatResponse(BaseModel):
    response: str
    request_id: UUID
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float


class OverviewResponse(BaseModel):
    total_requests: int
    error_rate: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    total_tokens: int
    estimated_cost: float


class LatencyPoint(BaseModel):
    timestamp: datetime
    p50: float
    p95: float
    p99: float


class TokenPoint(BaseModel):
    timestamp: datetime
    prompt_tokens: int
    completion_tokens: int


class RequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timestamp: datetime
    model: str
    prompt: str
    response: str | None
    status: str
    error_type: str | None
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: Decimal
    temperature: float | None
    max_tokens: int | None
    created_at: datetime


class PaginatedRequests(BaseModel):
    items: list[RequestResponse]
    total: int
    page: int
    page_size: int

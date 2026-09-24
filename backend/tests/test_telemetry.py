from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import LlmRequest
from app.telemetry import persist_telemetry


def test_persist_telemetry_calculates_total_tokens():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    request_id = uuid4()
    with Session(engine) as session:
        persist_telemetry(session, request_id=request_id, timestamp=datetime.now(timezone.utc), model="test-model", prompt="hello", response="world", status="success", error_type=None, latency_ms=42, prompt_tokens=2, completion_tokens=3, estimated_cost=0.000012, temperature=0.7, max_tokens=None)
        row = session.get(LlmRequest, request_id)
        assert row is not None
        assert row.total_tokens == 5
        assert row.status == "success"
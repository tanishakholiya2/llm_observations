CREATE TABLE IF NOT EXISTS llm_requests (
  id UUID PRIMARY KEY,
  timestamp TIMESTAMPTZ NOT NULL,
  model VARCHAR(120) NOT NULL,
  prompt TEXT NOT NULL,
  response TEXT,
  status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'error')),
  error_type VARCHAR(120),
  latency_ms INTEGER NOT NULL,
  prompt_tokens INTEGER NOT NULL DEFAULT 0,
  completion_tokens INTEGER NOT NULL DEFAULT 0,
  total_tokens INTEGER NOT NULL DEFAULT 0,
  estimated_cost NUMERIC(12, 8) NOT NULL DEFAULT 0,
  temperature NUMERIC(3, 2),
  max_tokens INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_llm_requests_timestamp ON llm_requests (timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_llm_requests_model ON llm_requests (model);
CREATE INDEX IF NOT EXISTS ix_llm_requests_status ON llm_requests (status);

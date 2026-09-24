const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export type Overview = { total_requests: number; error_rate: number; avg_latency_ms: number; p50_latency_ms: number; p95_latency_ms: number; p99_latency_ms: number; total_tokens: number; estimated_cost: number };
export type LatencyPoint = { timestamp: string; p50: number; p95: number; p99: number };
export type TokenPoint = { timestamp: string; prompt_tokens: number; completion_tokens: number };
export type RequestRow = { id: string; timestamp: string; model: string; prompt: string; response: string | null; status: string; error_type: string | null; latency_ms: number; prompt_tokens: number; completion_tokens: number; total_tokens: number; estimated_cost: number; temperature: number | null; max_tokens: number | null; created_at: string };
export type ChatResult = { response: string; request_id: string; latency_ms: number; prompt_tokens: number; completion_tokens: number; total_tokens: number; estimated_cost: number };

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const api = {
  overview: () => get<Overview>('/api/metrics/overview'),
  latency: () => get<LatencyPoint[]>('/api/metrics/latency'),
  tokens: () => get<TokenPoint[]>('/api/metrics/tokens'),
  requests: (status: string) => get<{ items: RequestRow[]; total: number; page: number; page_size: number }>(`/api/requests?page=1&page_size=50${status !== 'all' ? `&status=${status}` : ''}`),
  chat: async (body: { prompt: string; model: string; temperature: number }) => {
    const response = await fetch(`${API_URL}/api/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'LLM request failed');
    return data as ChatResult;
  }
};

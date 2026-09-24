from dataclasses import dataclass

import httpx

from .config import get_settings
from .cost import estimate_cost, estimate_tokens


@dataclass
class Completion:
    response: str
    prompt_tokens: int
    completion_tokens: int
    estimated_cost: float


async def complete(prompt: str, model: str, temperature: float, max_tokens: int | None) -> Completion:
    settings = get_settings()
    if settings.llm_api_url:
        headers = {"Content-Type": "application/json"}
        if settings.llm_api_key:
            headers["Authorization"] = f"Bearer {settings.llm_api_key}"
        async with httpx.AsyncClient(timeout=60) as client:
            result = await client.post(settings.llm_api_url, headers=headers, json={"model": model, "prompt": prompt, "temperature": temperature, "max_tokens": max_tokens})
            result.raise_for_status()
            data = result.json()
        response = data.get("response") or data.get("choices", [{}])[0].get("text", "")
        prompt_tokens = int(data.get("prompt_tokens", estimate_tokens(prompt)))
        completion_tokens = int(data.get("completion_tokens", estimate_tokens(response)))
    else:
        response = (f"A practical explanation of {prompt.rstrip('.?!')}: observe demand, compare it with a target, "
                    "and adjust capacity gradually. Use resource requests, limits, stabilization windows, and "
                    "latency/error dashboards so the system scales without oscillation.")
        prompt_tokens = estimate_tokens(prompt)
        completion_tokens = estimate_tokens(response)

    return Completion(response, prompt_tokens, completion_tokens, float(estimate_cost(prompt_tokens, completion_tokens)))

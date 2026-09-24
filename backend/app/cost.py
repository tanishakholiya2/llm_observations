from decimal import Decimal

# Default rates are deliberately explicit and easy to replace per model.
DEFAULT_INPUT_RATE = Decimal("0.000003")
DEFAULT_OUTPUT_RATE = Decimal("0.000006")


def estimate_cost(prompt_tokens: int, completion_tokens: int, input_rate: Decimal = DEFAULT_INPUT_RATE, output_rate: Decimal = DEFAULT_OUTPUT_RATE) -> Decimal:
    return (Decimal(prompt_tokens) * input_rate) + (Decimal(completion_tokens) * output_rate)


def estimate_tokens(text: str) -> int:
    return max(1, (len(text.strip()) + 3) // 4)

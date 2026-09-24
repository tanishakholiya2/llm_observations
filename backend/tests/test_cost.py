from decimal import Decimal

from app.cost import estimate_cost, estimate_tokens


def test_cost_calculation():
    assert estimate_cost(12, 143) == Decimal("0.000894")


def test_token_estimate_is_nonzero():
    assert estimate_tokens("hello") == 2

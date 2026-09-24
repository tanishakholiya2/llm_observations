from app.metrics import percentile


def test_percentile_interpolates():
    assert percentile([100, 200, 300, 400, 500], 0.5) == 300
    assert percentile([100, 200, 300, 400, 500], 0.95) == 480


def test_empty_percentile_is_zero():
    assert percentile([], 0.99) == 0

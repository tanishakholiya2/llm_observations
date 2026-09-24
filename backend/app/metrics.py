from collections.abc import Iterable
from datetime import datetime, timedelta


def percentile(values: Iterable[int | float], percentile_value: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    rank = (len(ordered) - 1) * percentile_value
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def bucket_hour(timestamp: datetime) -> datetime:
    return timestamp.replace(minute=0, second=0, microsecond=0)


def hours_between(start: datetime, end: datetime) -> list[datetime]:
    current = bucket_hour(start)
    end_bucket = bucket_hour(end)
    buckets: list[datetime] = []
    while current <= end_bucket:
        buckets.append(current)
        current += timedelta(hours=1)
    return buckets

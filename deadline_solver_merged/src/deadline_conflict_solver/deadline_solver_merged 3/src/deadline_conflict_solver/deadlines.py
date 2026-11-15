from __future__ import annotations
from __future__ import annotations
from datetime import date, timedelta


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def days_left(deadline: str, today: date | None = None) -> int:
    return (parse_date(deadline) - (today or date.today())).days


def daily_capacity(start: date, end: date, weekdays: float = 2.0,
                   weekends: float = 4.0, overrides: dict[date, float] | None = None):
    """Return per-date available study hours including optional overrides."""
    if end < start or weekdays < 0 or weekends < 0:
        raise ValueError('Invalid date range or hours')
    overrides = overrides or {}
    result = {}
    day = start
    while day <= end:
        result[day] = overrides.get(day, weekends if day.weekday() >= 5 else weekdays)
        day += timedelta(days=1)
    return result

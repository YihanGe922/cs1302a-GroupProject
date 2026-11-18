"""Convert input dictionaries into the planning model."""
from __future__ import annotations
from datetime import date, timedelta
from .models import Task

DAY_NAMES = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')

def parse_payload(payload: dict):
    if not isinstance(payload, dict):
        raise ValueError('Input data must be a dictionary')
    try:
        start = date.fromisoformat(payload['start_date'])
        records = payload['assignments']
    except (KeyError, TypeError) as exc:
        raise ValueError('Provide start_date and assignments') from exc
    if not isinstance(records, list):
        raise ValueError('assignments must be a list')
    tasks = []
    for i, row in enumerate(records, 1):
        if not isinstance(row, dict):
            raise ValueError(f'Assignment {i} must be an object')
        try:
            identifier = str(row.get('id') or f'T{i}')
            name = str(row['name'])
            hours = float(row['estimated_hours'])
            deadline = date.fromisoformat(row['deadline'])
            priority = int(row.get('priority', 3))
            deps = row.get('depends_on', [])
            if not isinstance(deps, list):
                raise ValueError('depends_on must be a list')
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f'Invalid assignment {i}: {exc}') from exc
        tasks.append(Task(identifier, name, hours, deadline, priority, deps))
    if not tasks:
        raise ValueError('At least one assignment is required')
    end = max(t.deadline for t in tasks)
    raw_cap = payload.get('daily_free_time', 3)
    overrides = payload.get('date_overrides', {})
    if not isinstance(overrides, dict):
        raise ValueError('date_overrides must be a dictionary')
    cap = {}
    day = start
    while day <= end:
        if isinstance(raw_cap, (int, float)):
            available = float(raw_cap)
        elif isinstance(raw_cap, dict):
            key = DAY_NAMES[day.weekday()]
            available = float(raw_cap.get(key, raw_cap.get('default', 0)))
        else:
            raise ValueError('daily_free_time must be a number or weekday dictionary')
        available = float(overrides.get(day.isoformat(), available))
        if available < 0:
            raise ValueError('Available hours cannot be negative')
        cap[day] = available
        day += timedelta(days=1)
    buffer_ratio = float(payload.get('buffer_ratio', 0.1))
    if not 0 <= buffer_ratio < 1:
        raise ValueError('buffer_ratio must be between 0 and 1 (exclusive)')
    return start, tasks, cap, buffer_ratio

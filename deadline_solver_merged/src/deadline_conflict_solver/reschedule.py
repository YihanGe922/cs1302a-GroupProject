from __future__ import annotations
from __future__ import annotations
from datetime import date
from .models import Task, PlanResult
from .planner import make_plan


def suggest_extra_hours(tasks: list[Task], capacities: dict[date, float],
                        start: date, max_extra: float = 3.0,
                        step: float = 0.5, buffer_ratio: float = 0.1):
    """Try equal extra time per day; return smallest tested feasible increase.

    Returns (extra_hours, result) or None. This is a scenario comparison,
    not proof that the proposed plan is optimal.
    """
    if max_extra < 0 or step <= 0:
        raise ValueError('Invalid scenario range')
    n = int(round(max_extra / step))
    for i in range(n + 1):
        extra = round(i * step, 6)
        expanded = {d: h + extra for d, h in capacities.items()}
        result = make_plan(tasks, expanded, start, buffer_ratio)
        if not result.conflicts:
            return extra, result
    return None

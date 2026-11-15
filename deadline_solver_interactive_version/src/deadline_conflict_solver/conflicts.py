from __future__ import annotations
from datetime import date
from .models import Task, PlanResult


def analyze_conflicts(tasks: list[Task], result: PlanResult) -> list[dict]:
    """Produce user-facing diagnostics from a computed plan."""
    reports = []
    for task in tasks:
        missed = round(result.remaining[task.id], 2)
        if missed > 0:
            reports.append({'task_id': task.id, 'name': task.name,
                            'hours_short': missed,
                            'deadline': task.deadline.isoformat(),
                            'reason': 'Insufficient available time or blocked by prerequisites'})
    return reports

from __future__ import annotations
from datetime import date, timedelta
from .models import Task, WorkBlock, PlanResult

EPS = 1e-8


def validate_tasks(tasks: list[Task], start: date):
    ids = [t.id for t in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError('Task IDs must be unique')
    by_id = {t.id: t for t in tasks}
    for task in tasks:
        if task.deadline < start:
            raise ValueError(f'{task.id} has a deadline before start date')
        if task.id in task.depends_on:
            raise ValueError(f'{task.id} cannot depend on itself')
        for dep in task.depends_on:
            if dep not in by_id:
                raise ValueError(f'Unknown dependency {dep} for {task.id}')
            if by_id[dep].deadline > task.deadline:
                # Not impossible, but a warning-worthy inconsistent deadline.
                pass
    visited, active = set(), set()

    def visit(task_id):
        if task_id in active:
            raise ValueError('Circular dependency detected')
        if task_id in visited:
            return
        active.add(task_id)
        for dep in by_id[task_id].depends_on:
            visit(dep)
        active.remove(task_id)
        visited.add(task_id)

    for task_id in ids:
        visit(task_id)


def make_plan(tasks: list[Task], capacities: dict[date, float], start: date,
              buffer_ratio: float = 0.1) -> PlanResult:
    """Schedule in 0.5h chunks, with priority/deadline ordering and strict prerequisites.

    Days use capacity after an optional buffer. This is a heuristic, not an
    optimal scheduling solver. A task may be split across days, and a task
    depending on another can begin only after its prerequisite finishes.
    """
    if not 0 <= buffer_ratio < 1:
        raise ValueError('buffer_ratio must be in [0, 1)')
    validate_tasks(tasks, start)
    for d, hours in capacities.items():
        if hours < 0:
            raise ValueError(f'Negative capacity for {d}')
    if not tasks:
        return PlanResult([], {}, {}, [])

    end = max(task.deadline for task in tasks)
    remaining = {task.id: float(task.hours) for task in tasks}
    completed_on = {}
    blocks = []
    day = start
    by_id = {task.id: task for task in tasks}
    while day <= end:
        free = max(0.0, capacities.get(day, 0.0) * (1 - buffer_ratio))
        # Fill up to available half-hour-sized blocks; no work beyond deadline.
        while free > EPS:
            eligible = [t for t in tasks if remaining[t.id] > EPS and
                        t.deadline >= day and
                        all(remaining[dep] <= EPS for dep in t.depends_on)]
            if not eligible:
                break
            # earliest deadline first; priority breaks ties; then task ID
            task = min(eligible, key=lambda t: (t.deadline, t.priority, t.id))
            amount = min(0.5, free, remaining[task.id])
            blocks.append(WorkBlock(day, task.id, round(amount, 6)))
            remaining[task.id] -= amount
            free -= amount
            if remaining[task.id] <= EPS:
                remaining[task.id] = 0.0
                completed_on[task.id] = day
        day += timedelta(days=1)

    # Merge repeated task/day chunks for readable output
    merged = {}
    for b in blocks:
        merged[(b.day, b.task_id)] = merged.get((b.day, b.task_id), 0) + b.hours
    combined = [WorkBlock(d, tid, round(h, 6)) for (d, tid), h in merged.items()]
    conflicts = []
    for task in tasks:
        if remaining[task.id] > EPS:
            conflicts.append(f'{task.name}: {remaining[task.id]:.1f}h unfinished by {task.deadline.isoformat()}')
    return PlanResult(combined, remaining, completed_on, conflicts)

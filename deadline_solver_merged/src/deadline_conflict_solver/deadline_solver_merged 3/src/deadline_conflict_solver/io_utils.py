from __future__ import annotations
import csv
from datetime import date
from .models import Task, PlanResult


def load_tasks_csv(path: str) -> list[Task]:
    """Required headers: id,name,hours,deadline; optional priority,depends_on."""
    tasks = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            dependencies = [x.strip() for x in (row.get('depends_on') or '').split(';') if x.strip()]
            tasks.append(Task(id=row['id'], name=row['name'], hours=float(row['hours']),
                              deadline=date.fromisoformat(row['deadline']),
                              priority=int(row.get('priority') or 3),
                              depends_on=dependencies))
    return tasks


def export_schedule_csv(result: PlanResult, path: str):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'task_id', 'hours'])
        for b in result.blocks:
            writer.writerow([b.day.isoformat(), b.task_id, b.hours])


def format_plan(result: PlanResult) -> str:
    lines = [f'{b.day.isoformat()}: {b.task_id} — {b.hours:g}h' for b in result.blocks]
    lines += ['Conflicts:'] + (result.conflicts if result.conflicts else ['None'])
    return '\n'.join(lines)

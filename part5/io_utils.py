from __future__ import annotations
import csv
from datetime import date
from .models import Task, PlanResult
from .data import parse_payload

def load_tasks_csv(path: str) -> tuple[date, list[Task], dict[date, float], float]:
    """
    Load tasks from CSV file and validate via parse_payload.
    Required CSV headers: id,name,hours,deadline
    Optional headers: priority,depends_on
    CSV does NOT store start_date, daily_free_time, buffer_ratio.
    We will use default values here; you can pass your own in CLI.
    """
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        required_cols = {"id", "name", "hours", "deadline"}
        if not required_cols.issubset(reader.fieldnames or []):
            missing = required_cols - set(reader.fieldnames or [])
            raise ValueError(f"CSV missing required columns: {', '.join(missing)}")

        assignments = []
        for row in reader:
            dependencies = [x.strip() for x in (row.get('depends_on') or '').split(';') if x.strip()]
            assignments.append({
                "id": row["id"],
                "name": row["name"],
                "estimated_hours": row["hours"],
                "deadline": row["deadline"],
                "priority": row.get("priority", 3),
                "depends_on": dependencies
            })

    # build payload dict and reuse all validation logic from data.py
    payload = {
        "start_date": date.today().isoformat(),
        "assignments": assignments,
        "daily_free_time": 3,
        "buffer_ratio": 0.1
    }
    return parse_payload(payload)

def export_schedule_csv(result: PlanResult, path: str):
    """Export the solved schedule blocks to CSV."""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'task_id', 'hours'])
        for b in result.blocks:
            writer.writerow([b.day.isoformat(), b.task_id, b.hours])

def format_plan(result: PlanResult) -> str:
    """Format schedule result to human-readable text string."""
    lines = [f'{b.day.isoformat()}: {b.task_id} — {b.hours:g}h' for b in result.blocks]
    lines += ['Conflicts:'] + (result.conflicts if result.conflicts else ['None'])
    return '\n'.join(lines)

# ========== 新增：增删改任务函数（满足成员5验收要求） ==========
def add_task(task_list: list[Task], new_task: Task) -> None:
    """Add a new task in-place; raise error if ID already exists."""
    existing_ids = {t.id for t in task_list}
    if new_task.id in existing_ids:
        raise ValueError(f"Task id {new_task.id} already exists.")
    task_list.append(new_task)

def remove_task(task_list: list[Task], task_id: str) -> None:
    """Remove task by id; raise error if not found."""
    for idx, t in enumerate(task_list):
        if t.id == task_id:
            del task_list[idx]
            return
    raise ValueError(f"Task id {task_id} not found.")

def update_task(task_list: list[Task], task_id: str, **kwargs) -> None:
    """
    Update fields of an existing task.
    Supported kwargs: name, hours, deadline, priority, depends_on
    """
    for t in task_list:
        if t.id == task_id:
            if "name" in kwargs:
                t.name = kwargs["name"]
            if "hours" in kwargs:
                t.hours = float(kwargs["hours"])
            if "deadline" in kwargs:
                t.deadline = date.fromisoformat(kwargs["deadline"])
            if "priority" in kwargs:
                t.priority = int(kwargs["priority"])
            if "depends_on" in kwargs:
                t.depends_on = list(kwargs["depends_on"])
            return
    raise ValueError(f"Task id {task_id} not found.")

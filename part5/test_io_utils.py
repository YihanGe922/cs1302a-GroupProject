"""
Test cases for io_utils.py
CSV load, add / remove / update task
Member 5
"""
import pytest
import tempfile
from datetime import date
from deadline_solver.io_utils import load_tasks_csv, add_task, remove_task, update_task
from deadline_solver.models import Task

def test_csv_load_missing_required_column():
    csv_content = "id,name,hours\nT1,Homework,2"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
    with pytest.raises(ValueError, match="CSV missing required columns"):
        load_tasks_csv(f.name)

def test_add_duplicate_task():
    tasks = [Task("T1", "Math", 2, date.fromisoformat("2026-11-20"))]
    new_task = Task("T1", "Essay", 1, date.fromisoformat("2026-11-21"))
    with pytest.raises(ValueError, match="Task id T1 already exists"):
        add_task(tasks, new_task)

def test_remove_nonexistent_task():
    tasks = [Task("T1", "Math", 2, date.fromisoformat("2026-11-20"))]
    with pytest.raises(ValueError, match="Task id T99 not found"):
        remove_task(tasks, "T99")

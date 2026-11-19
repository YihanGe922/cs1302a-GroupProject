from __future__ import annotations
from datetime import date, timedelta
from .models import Task, WorkBlock, PlanResult

EPS = 1e-8

def validate_tasks(tasks: list[Task], start: date):
    # 保持原样不变
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

    # ================= 新增：计算有效截止日期 (Effective Deadline) =================
    by_id = {task.id: task for task in tasks}
    effective_deadlines = {task.id: task.deadline for task in tasks}
    visited = set()

    def calc_effective_deadline(task_id):
        if task_id in visited:
            return effective_deadlines[task_id]
        visited.add(task_id)
        
        task = by_id[task_id]
        max_dep_deadline = task.deadline
        # 遍历所有前置依赖，取依赖链中最晚的截止日期
        for dep_id in task.depends_on:
            dep_deadline = calc_effective_deadline(dep_id)
            if dep_deadline > max_dep_deadline:
                max_dep_deadline = dep_deadline
                
        effective_deadlines[task_id] = max_dep_deadline
        return max_dep_deadline

    # 为所有任务计算 effective_deadline (由于 validate_tasks 已检查过循环依赖，这里递归绝对安全)
    for task in tasks:
        calc_effective_deadline(task.id)
    # ==============================================================================

    end = max(task.deadline for task in tasks)
    remaining = {task.id: float(task.hours) for task in tasks}
    completed_on = {}
    blocks = []
    day = start
    
    while day <= end:
        free = max(0.0, capacities.get(day, 0.0) * (1 - buffer_ratio))
        # Fill up to available half-hour-sized blocks; no work beyond deadline.
        while free > EPS:
            eligible = [t for t in tasks if remaining[t.id] > EPS and
                        t.deadline >= day and
                        all(remaining[dep] <= EPS for dep in t.depends_on)]
            if not eligible:
                break
            
            # 修改点：排序策略改为使用 effective_deadline
            # 原本是: key=lambda t: (t.deadline, t.priority, t.id)
            # 现在改为: 优先看有效截止日期，其次看优先级，最后看 ID
            task = min(eligible, key=lambda t: (effective_deadlines[t.id], t.priority, t.id))
            
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

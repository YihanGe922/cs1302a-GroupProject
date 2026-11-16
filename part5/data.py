Python 3.14.7 (tags/v3.14.7:823f032, Aug  5 2026, 10:51:32) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
>>> """Convert input dictionaries into the planning model.
... No JSON file I/O here. JSON read/write belongs to io_utils.py
... """
... from __future__ import annotations
... from datetime import date, timedelta
... from .models import Task
... 
... DAY_NAMES = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
... 
... def parse_payload(payload: dict):
...     if not isinstance(payload, dict):
...         raise ValueError('Input data must be a dictionary')
... 
...     try:
...         start = date.fromisoformat(payload['start_date'])
...         records = payload['assignments']
...     except KeyError as exc:
...         raise ValueError(f'Missing required top-level key: {exc}. Please provide start_date and assignments') from exc
...     except TypeError as exc:
...         raise ValueError('start_date must be an ISO date string, assignments must be a list') from exc
... 
...     if not isinstance(records, list):
...         raise ValueError('"assignments" must be a list of task objects')
... 
...     tasks = []
...     task_id_set = set()
... 
...     for i, row in enumerate(records, 1):
...         if not isinstance(row, dict):
...             raise ValueError(f'Assignment {i}: must be an object (dict)')
... 
...         identifier = str(row.get('id') or f'T{i}')
...         # 重复ID校验
...         if identifier in task_id_set:
            raise ValueError(f'Assignment {i}: Duplicate task ID "{identifier}". Task IDs must be unique.')
        task_id_set.add(identifier)

        try:
            name = str(row['name'])
            hours = float(row['estimated_hours'])
            deadline = date.fromisoformat(row['deadline'])
            priority = int(row.get('priority', 3))
            deps = row.get('depends_on', [])
        except KeyError as exc:
            raise ValueError(f'Assignment {i}: Missing required field "{exc}"') from exc
        except (TypeError, ValueError) as exc:
            raise ValueError(f'Assignment {i}: Invalid value for field: {exc}') from exc

        # 数值合法性校验
        if hours <= 0:
            raise ValueError(f'Assignment {i}: estimated_hours must be > 0, got {hours}')
        if priority < 1 or priority > 5:
            raise ValueError(f'Assignment {i}: priority should be between 1~5 (1 highest,5 lowest)')
        if not isinstance(deps, list):
            raise ValueError(f'Assignment {i}: depends_on must be a list of task ids')

        tasks.append(Task(identifier, name, hours, deadline, priority, deps))

    if not tasks:
        raise ValueError('At least one assignment is required in assignments list')

    end = max(t.deadline for t in tasks)
    raw_cap = payload.get('daily_free_time', 3)
    overrides = payload.get('date_overrides', {})

    if not isinstance(overrides, dict):
        raise ValueError('"date_overrides" must be a dictionary mapping ISO date strings to available hours')

    cap = {}
    day = start
    while day <= end:
        if isinstance(raw_cap, (int, float)):
            available = float(raw_cap)
        elif isinstance(raw_cap, dict):
            key = DAY_NAMES[day.weekday()]
            available = float(raw_cap.get(key, raw_cap.get('default', 0)))
        else:
            raise ValueError('daily_free_time must be a number, or a weekday dictionary')

        available = float(overrides.get(day.isoformat(), available))
        if available < 0:
            raise ValueError(f'Date {day.isoformat()}: available hours cannot be negative, got {available}')
        cap[day] = available
        day += timedelta(days=1)

    buffer_ratio = float(payload.get('buffer_ratio', 0.1))
    if not (0 <= buffer_ratio < 1):
        raise ValueError(f'buffer_ratio must be 0 ≤ buffer_ratio <1, got {buffer_ratio}')

    # 校验依赖任务ID是否存在
    all_task_ids = {t.id for t in tasks}
    for idx, t in enumerate(tasks, 1):
        for dep_id in t.depends_on:
            if dep_id not in all_task_ids:
                raise ValueError(f'Assignment {idx} ("{t.name}") depends on non-existent task id "{dep_id}"')


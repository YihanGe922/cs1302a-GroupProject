    # ================= 修正：反向传播计算有效截止日期 =================
    by_id = {task.id: task for task in tasks}
    effective_deadlines = {task.id: task.deadline for task in tasks}
    
    # 由于 validate_tasks 已经保证了无循环依赖，我们可以直接进行多轮传播
    changed = True
    while changed:
        changed = False
        for task in tasks:
            for dep_id in task.depends_on:
                # 核心逻辑：如果依赖方(task)的截止日期更早，被依赖方(dep)的 deadline 必须被压缩
                if effective_deadlines[task.id] < effective_deadlines[dep_id]:
                    effective_deadlines[dep_id] = effective_deadlines[task.id]
                    changed = True
    # ==============================================================================
    
    # 后面的排序逻辑不变：
    # task = min(eligible, key=lambda t: (effective_deadlines[t.id], t.priority, t.id))

    # ================= 修正：反向传播计算有效截止日期 =================
    by_id = {task.id: task for task in tasks}
    # 初始化：每个人先用自己的截止日期
    effective_deadlines = {task.id: task.deadline for task in tasks}
    
    # 使用循环传播，直到所有依赖链上的截止日期都收敛（即没有变化为止）
    changed = True
    while changed:
        changed = False
        for task in tasks:
            for dep_id in task.depends_on:
                # 核心逻辑：如果当前的 task 截止更早，那么它依赖的 dep 必须更早完成
                # 所以 dep 的有效 deadline 被压缩（取最小值）
                if effective_deadlines[task.id] < effective_deadlines[dep_id]:
                    effective_deadlines[dep_id] = effective_deadlines[task.id]
                    changed = True
    # ==============================================================================

    end = max(task.deadline for task in tasks)
    # ... 后面的排期循环保持不变 ...
    
    # 在 while free > EPS 内部，修改排序键：
    task = min(eligible, key=lambda t: (effective_deadlines[t.id], t.priority, t.id))

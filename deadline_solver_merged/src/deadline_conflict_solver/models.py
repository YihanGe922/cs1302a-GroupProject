from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    id: str
    name: str
    hours: float
    deadline: date
    priority: int = 3  # 1 highest; 5 lowest
    depends_on: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.id.strip() or not self.name.strip():
            raise ValueError('Task ID and name must not be blank')
        if self.hours <= 0:
            raise ValueError('Required hours must be positive')
        if self.priority not in range(1, 6):
            raise ValueError('Priority must be between 1 and 5')


@dataclass
class WorkBlock:
    day: date
    task_id: str
    hours: float


@dataclass
class PlanResult:
    blocks: list[WorkBlock]
    remaining: dict[str, float]
    completed_on: dict[str, date]
    conflicts: list[str]

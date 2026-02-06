from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PodStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"


class NodeStatus(str, Enum):
    READY = "ready"
    NOT_READY = "not_ready"


@dataclass
class Pod:
    pod_id: str
    cpu_req: int
    mem_req: int
    status: PodStatus = PodStatus.PENDING
    node_id: Optional[str] = None  # assigned node


@dataclass
class Node:
    node_id: str
    cpu_capacity: int
    mem_capacity: int
    status: NodeStatus = NodeStatus.READY
    pods: List[Pod] = field(default_factory=list)

    @property
    def cpu_used(self) -> int:
        return sum(p.cpu_req for p in self.pods if p.status == PodStatus.RUNNING)

    @property
    def mem_used(self) -> int:
        return sum(p.mem_req for p in self.pods if p.status == PodStatus.RUNNING)

    def can_fit(self, pod: Pod) -> bool:
        if self.status != NodeStatus.READY:
            return False
        return (self.cpu_used + pod.cpu_req <= self.cpu_capacity) and (
            self.mem_used + pod.mem_req <= self.mem_capacity
        )

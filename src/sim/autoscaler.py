from __future__ import annotations
from dataclasses import dataclass
from typing import List

from .models import Node, NodeStatus


@dataclass
class Autoscaler:
    cpu_threshold: float = 0.80  # e.g. 80%
    max_nodes: int = 10

    def avg_cpu_utilisation(self, nodes: List[Node]) -> float:
        ready = [n for n in nodes if n.status == NodeStatus.READY]
        if not ready:
            return 0.0
        utilisation = [(n.cpu_used / n.cpu_capacity) if n.cpu_capacity else 0.0 for n in ready]
        return sum(utilisation) / len(utilisation)

    def should_scale_out(self, nodes: List[Node]) -> bool:
        if len(nodes) >= self.max_nodes:
            return False
        return self.avg_cpu_utilisation(nodes) > self.cpu_threshold

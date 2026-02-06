from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from .models import Node, Pod, PodStatus


class SchedulingAlgorithm(str):
    ROUND_ROBIN = "round_robin"
    BIN_PACKING = "bin_packing"


@dataclass
class Scheduler:
    algorithm: str = SchedulingAlgorithm.ROUND_ROBIN
    _rr_index: int = 0

    def schedule(self, pod: Pod, nodes: List[Node]) -> Optional[Node]:
        # Only schedule pending pods
        if pod.status != PodStatus.PENDING:
            return None

        ready_nodes = [n for n in nodes if n.can_fit(pod)]
        if not ready_nodes:
            return None

        if self.algorithm == SchedulingAlgorithm.ROUND_ROBIN:
            node = ready_nodes[self._rr_index % len(ready_nodes)]
            self._rr_index += 1
            return node

        # Bin packing: choose the node that will have the least remaining CPU after placement
        if self.algorithm == SchedulingAlgorithm.BIN_PACKING:
            def remaining_cpu_after(n: Node) -> int:
                return (n.cpu_capacity - (n.cpu_used + pod.cpu_req))
            return sorted(ready_nodes, key=remaining_cpu_after)[0]

        # Default fallback
        return ready_nodes[0]

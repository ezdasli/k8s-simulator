from __future__ import annotations
from dataclasses import dataclass
from typing import List

from .models import Node, NodeStatus, Pod, PodStatus


@dataclass
class ControllerManager:
    """
    Responsible for recovery actions:
    - if node crashes, pods on it become PENDING again
    - if a pod fails, reschedule it (set to PENDING)
    """

    def handle_node_failure(self, node: Node) -> List[Pod]:
        node.status = NodeStatus.NOT_READY
        affected = []
        for p in node.pods:
            p.status = PodStatus.PENDING
            p.node_id = None
            affected.append(p)
        node.pods.clear()
        return affected

    def handle_pod_failure(self, pod: Pod) -> Pod:
        pod.status = PodStatus.PENDING
        pod.node_id = None
        return pod

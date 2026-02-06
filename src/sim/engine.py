from __future__ import annotations
from dataclasses import dataclass
from typing import List
import itertools

from .models import Node, Pod, PodStatus, NodeStatus
from .scheduler import Scheduler
from .autoscaler import Autoscaler
from .controller import ControllerManager
from .logging import EventLogger


@dataclass
class SimulationConfig:
    node_cpu: int = 8
    node_mem: int = 16
    autoscale_threshold: float = 0.80


class SimulationEngine:
    def __init__(self, cfg: SimulationConfig, scheduler: Scheduler, autoscaler: Autoscaler):
        self.cfg = cfg
        self.scheduler = scheduler
        self.autoscaler = autoscaler
        self.controller = ControllerManager()
        self.logger = EventLogger()

        self.nodes: List[Node] = []
        self.pods: List[Pod] = []
        self._node_counter = itertools.count(1)
        self._pod_counter = itertools.count(1)

    def add_node(self) -> Node:
        node = Node(
            node_id=f"node-{next(self._node_counter)}",
            cpu_capacity=self.cfg.node_cpu,
            mem_capacity=self.cfg.node_mem,
            status=NodeStatus.READY,
        )
        self.nodes.append(node)
        self.logger.log("scale_out", node_id=node.node_id)
        return node

    def add_pod(self, cpu_req: int, mem_req: int) -> Pod:
        pod = Pod(pod_id=f"pod-{next(self._pod_counter)}", cpu_req=cpu_req, mem_req=mem_req)
        self.pods.append(pod)
        self.logger.log("pod_created", pod_id=pod.pod_id, cpu=cpu_req, mem=mem_req)
        return pod

    def tick(self) -> None:
        # 1) Schedule pending pods
        for pod in [p for p in self.pods if p.status == PodStatus.PENDING]:
            node = self.scheduler.schedule(pod, self.nodes)
            if node:
                pod.status = PodStatus.RUNNING
                pod.node_id = node.node_id
                node.pods.append(pod)
                self.logger.log("scheduled", pod_id=pod.pod_id, node_id=node.node_id)

        # 2) Autoscale if needed
        if self.autoscaler.should_scale_out(self.nodes):
            self.add_node()

    # Fault injection
    def crash_node(self, node_id: str) -> None:
        node = next((n for n in self.nodes if n.node_id == node_id), None)
        if not node:
            return
        affected = self.controller.handle_node_failure(node)
        self.logger.log("node_crash", node_id=node_id, affected_pods=[p.pod_id for p in affected])

    def fail_pod(self, pod_id: str) -> None:
        pod = next((p for p in self.pods if p.pod_id == pod_id), None)
        if not pod:
            return
        # remove from node if running
        if pod.node_id:
            node = next((n for n in self.nodes if n.node_id == pod.node_id), None)
            if node:
                node.pods = [p for p in node.pods if p.pod_id != pod_id]
        pod.status = PodStatus.FAILED
        self.logger.log("pod_failed", pod_id=pod_id)

        # recovery: reschedule
        self.controller.handle_pod_failure(pod)
        self.logger.log("pod_recovered_to_pending", pod_id=pod_id)

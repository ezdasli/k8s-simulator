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
        self.deployments = {}
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

    def add_pod(self, cpu_req: int, mem_req: int,pod_id: str | None = None) -> Pod:
        if pod_id is None:
            pod_id = f"pod-{next(self._pod_counter)}"

        pod = Pod(
            pod_id=pod_id,
            cpu_req=cpu_req,
            mem_req=mem_req,
        )

        self.pods.append(pod)
        self.logger.log("pod_created", pod_id=pod.pod_id, cpu=cpu_req, mem=mem_req)

        return pod
    
    def create_deployment(
        self,
        name: str,
        replicas: int,
        cpu_req: int,
        mem_req: int,
    ) -> List[Pod]:
        
        self.deployments[name] = {
            "replicas": replicas,
            "cpu_req": cpu_req,
            "mem_req": mem_req,
        }

        created_pods = []

        for i in range(replicas):

            pod_name = f"{name}-{i+1}"

            pod = self.add_pod(cpu_req, mem_req, pod_id=pod_name)

            # optional metadata (useful for UI later)
            pod.owner_kind = "Deployment"
            pod.owner_name = name

            created_pods.append(pod)

        # log event
        self.logger.log(
            "deployment_created",
            pod_id=name,
            cpu=cpu_req,
            mem=mem_req,
        )

        return created_pods
    
    def reconcile_deployments(self) -> None:
        for name, spec in self.deployments.items():
            active_pods = [
                p for p in self.pods
                if getattr(p, "owner_name", None) == name
                and p.status != PodStatus.FAILED
            ]

            missing = spec["replicas"] - len(active_pods)

            for i in range(missing):
                pod_name = f"{name}-recovered-{next(self._pod_counter)}"

                pod = self.add_pod(
                    cpu_req=spec["cpu_req"],
                    mem_req=spec["mem_req"],
                    pod_id=pod_name,
                )

                pod.owner_kind = "Deployment"
                pod.owner_name = name

                self.logger.log(
                    "deployment_reconciled",
                    pod_id=pod.pod_id,
                    deployment=name,
                )            

    def tick(self) -> None:
        self.reconcile_deployments()

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
        pod.node_id = None

        self.logger.log("pod_recovered_to_pending", pod_id=pod_id)

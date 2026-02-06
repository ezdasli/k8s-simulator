import streamlit as st
import pandas as pd

from sim.engine import SimulationConfig, SimulationEngine
from sim.scheduler import Scheduler, SchedulingAlgorithm
from sim.autoscaler import Autoscaler
from sim.models import PodStatus, NodeStatus


st.set_page_config(page_title="K8s Cluster Simulator", layout="wide")

# --- Session state init ---
if "engine" not in st.session_state:
    cfg = SimulationConfig(node_cpu=8, node_mem=16, autoscale_threshold=0.80)
    scheduler = Scheduler(algorithm=SchedulingAlgorithm.ROUND_ROBIN)
    autoscaler = Autoscaler(cpu_threshold=0.80, max_nodes=10)
    eng = SimulationEngine(cfg, scheduler, autoscaler)
    eng.add_node()
    st.session_state.engine = eng

eng: SimulationEngine = st.session_state.engine

st.title("Kubernetes Cluster Simulator (Educational)")

# --- Sidebar config ---
st.sidebar.header("Simulation Controls")
algo = st.sidebar.selectbox("Scheduling algorithm", [SchedulingAlgorithm.ROUND_ROBIN, SchedulingAlgorithm.BIN_PACKING])
eng.scheduler.algorithm = algo

node_cpu = st.sidebar.slider("Node CPU capacity", 2, 64, eng.cfg.node_cpu)
node_mem = st.sidebar.slider("Node Memory capacity", 2, 256, eng.cfg.node_mem)
threshold = st.sidebar.slider("Autoscale CPU threshold", 0.1, 0.95, float(eng.autoscaler.cpu_threshold))

if st.sidebar.button("Apply config"):
    eng.cfg.node_cpu = node_cpu
    eng.cfg.node_mem = node_mem
    eng.autoscaler.cpu_threshold = threshold
    st.sidebar.success("Config applied.")

st.sidebar.divider()
st.sidebar.subheader("Workload")
cpu_req = st.sidebar.slider("New pod CPU req", 1, 16, 2)
mem_req = st.sidebar.slider("New pod Mem req", 1, 64, 2)
if st.sidebar.button("Create Pod"):
    eng.add_pod(cpu_req=cpu_req, mem_req=mem_req)

if st.sidebar.button("Tick (advance simulation)"):
    eng.tick()

st.sidebar.divider()
st.sidebar.subheader("Fault injection")
node_ids = [n.node_id for n in eng.nodes]
pod_ids = [p.pod_id for p in eng.pods]
crash_node_id = st.sidebar.selectbox("Crash node", node_ids) if node_ids else None
fail_pod_id = st.sidebar.selectbox("Fail pod", pod_ids) if pod_ids else None

col_f1, col_f2 = st.sidebar.columns(2)
if col_f1.button("Crash Node") and crash_node_id:
    eng.crash_node(crash_node_id)
if col_f2.button("Fail Pod") and fail_pod_id:
    eng.fail_pod(fail_pod_id)

# --- Metrics ---
st.subheader("Cluster Utilisation")
avg_cpu = eng.autoscaler.avg_cpu_utilisation(eng.nodes)
st.metric("Average CPU utilisation", f"{avg_cpu*100:.1f}%")
st.write("Autoscaler scales out if avg CPU > threshold.")

# --- Topology view ---
st.subheader("Cluster Topology (Pods nested within Nodes)")

def status_badge(text: str, ok: bool) -> str:
    bg = "#2ecc71" if ok else "#e74c3c"
    return f"<span style='background:{bg};color:white;padding:2px 8px;border-radius:12px;font-size:12px;'>{text}</span>"

node_cols = st.columns(max(1, min(4, len(eng.nodes))))
for idx, node in enumerate(eng.nodes):
    with node_cols[idx % len(node_cols)]:
        node_ok = node.status == NodeStatus.READY
        st.markdown(
            f"### {node.node_id} {status_badge(node.status.value, node_ok)}",
            unsafe_allow_html=True
        )
        st.progress(min(1.0, node.cpu_used / node.cpu_capacity) if node.cpu_capacity else 0.0, text=f"CPU: {node.cpu_used}/{node.cpu_capacity}")
        st.progress(min(1.0, node.mem_used / node.mem_capacity) if node.mem_capacity else 0.0, text=f"MEM: {node.mem_used}/{node.mem_capacity}")

        if not node.pods:
            st.caption("No pods assigned")
        for p in node.pods:
            p_ok = p.status == PodStatus.RUNNING
            st.markdown(
                f"- **{p.pod_id}** {status_badge(p.status.value, p_ok)} (cpu={p.cpu_req}, mem={p.mem_req})",
                unsafe_allow_html=True
            )

# --- Pending pods ---
pending = [p for p in eng.pods if p.status == PodStatus.PENDING]
failed = [p for p in eng.pods if p.status == PodStatus.FAILED]
col_p, col_x = st.columns(2)
with col_p:
    st.subheader("Pending Pods")
    if pending:
        for p in pending:
            st.write(f"{p.pod_id} (cpu={p.cpu_req}, mem={p.mem_req})")
    else:
        st.caption("None")

with col_x:
    st.subheader("Failed Pods (transient)")
    if failed:
        for p in failed:
            st.write(p.pod_id)
    else:
        st.caption("None")

# --- Logs + export ---
st.subheader("Event Log")
df = eng.logger.to_dataframe()
st.dataframe(df, use_container_width=True)

if st.button("Export CSV"):
    path = "simulation_log.csv"
    eng.logger.export_csv(path)
    st.success("Exported simulation_log.csv (saved in project folder).")

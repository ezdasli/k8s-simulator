import streamlit as st
import pandas as pd
import yaml
import plotly.express as px

from sim.engine import SimulationConfig, SimulationEngine
from sim.scheduler import Scheduler, SchedulingAlgorithm
from sim.autoscaler import Autoscaler
from sim.models import PodStatus, NodeStatus


st.set_page_config(page_title="K8s Cluster Simulator", layout="wide")

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-left: 3rem;
    padding-right: 3rem;
    max-width: 1400px;
}

[data-testid="stMetric"] {
    background-color: #F3F6FA;
    border: 1px solid #E1E7EF;
    padding: 18px;
    border-radius: 14px;
}

.section-card {
    background-color: #FFFFFF;
    border: 1px solid #E1E7EF;
    border-radius: 16px;
    padding: 22px;
    margin-bottom: 22px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.node-card {
    background-color: #F8FAFC;
    border: 1px solid #DDE5EF;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 14px;
}
</style>
""", unsafe_allow_html=True)

# --- Session state init ---
if "engine" not in st.session_state:
    cfg = SimulationConfig(node_cpu=8, node_mem=16, autoscale_threshold=0.80)
    scheduler = Scheduler(algorithm=SchedulingAlgorithm.ROUND_ROBIN)
    autoscaler = Autoscaler(cpu_threshold=0.80, max_nodes=10)
    eng = SimulationEngine(cfg, scheduler, autoscaler)
    eng.add_node()
    st.session_state.engine = eng

eng: SimulationEngine = st.session_state.engine

if "cpu_history" not in st.session_state:
    st.session_state.cpu_history = []

st.title("Kubernetes Cluster Simulator")

total_nodes = len(eng.nodes)
total_pods = len(eng.pods)
running_pods = len([p for p in eng.pods if p.status == PodStatus.RUNNING])
failed_pods = len([p for p in eng.pods if p.status == PodStatus.FAILED])

avg_cpu = eng.autoscaler.avg_cpu_utilisation(eng.nodes)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Nodes", total_nodes)
c2.metric("Pods", total_pods)
c3.metric("Running Pods", running_pods)
c4.metric("Failed", failed_pods)
c5.metric("Avg CPU", f"{avg_cpu * 100:.1f}%")

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

if st.sidebar.button("Reset Cluster"):
    cfg = SimulationConfig(
        node_cpu=eng.cfg.node_cpu,
        node_mem=eng.cfg.node_mem,
        autoscale_threshold=eng.autoscaler.cpu_threshold,
    )

    scheduler = Scheduler(
        algorithm=eng.scheduler.algorithm
    )

    autoscaler = Autoscaler(
        cpu_threshold=eng.autoscaler.cpu_threshold,
        max_nodes=10,
    )

    new_engine = SimulationEngine(
        cfg,
        scheduler,
        autoscaler,
    )

    new_engine.add_node()
    st.session_state.engine = new_engine
    st.success("Cluster reset successfully.")
    st.session_state.cpu_history = []
    st.rerun()    

st.sidebar.divider()
st.sidebar.subheader("Workload")

workload_type = st.sidebar.selectbox("Workload type", ["Pod", "Deployment"])
workload_name = st.sidebar.text_input("Workload name", value="web-app")
cpu_req = st.sidebar.slider("CPU request", 1, 16, 2)
mem_req = st.sidebar.slider("Memory request", 1, 64, 2)

if workload_type == "Deployment":
    replicas = st.sidebar.slider("Replicas", 1, 10, 3)

    if st.sidebar.button("Create Deployment"):
        created = eng.create_deployment(
            name=workload_name,
            replicas=replicas,
            cpu_req=cpu_req,
            mem_req=mem_req,
        )
        st.sidebar.success(f"Deployment '{workload_name}' created with {len(created)} pods.")
else:
    if st.sidebar.button("Create Pod"):
        pod = eng.add_pod(cpu_req=cpu_req, mem_req=mem_req)
        pod.pod_id = workload_name
        st.sidebar.success(f"Pod '{workload_name}' created.")

with st.expander("Deploy from YAML", expanded=False):

    yaml_text = st.text_area(
        "Paste Deployment YAML",
        height=180,
        placeholder="""
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  resources:
    cpu: 2
    memory: 2
"""
    )


if st.button("Create Deployment from YAML"):

    if not yaml_text:

        st.warning("Please paste a YAML configuration.")

    else:

        try:

            config = yaml.safe_load(yaml_text)

            name = config.get("metadata", {}).get("name")
            replicas = config.get("spec", {}).get("replicas")
            cpu = config.get("spec", {}).get("resources", {}).get("cpu")
            mem = config.get("spec", {}).get("resources", {}).get("memory")

            if None in [name, replicas, cpu, mem]:

                st.error(
                    "Invalid YAML: Missing required fields "
                    "(name, replicas, cpu, memory)."
                )

            else:

                eng.create_deployment(
                    name=name,
                    replicas=replicas,
                    cpu_req=cpu,
                    mem_req=mem,
                )

                st.success(
                    f"Deployment '{name}' created from YAML."
                )

        except Exception as e:

            st.error(
                f"Invalid YAML format: {e}"
            )        

if st.sidebar.button("Tick (advance simulation)"):
    eng.tick()

    current_cpu = eng.autoscaler.avg_cpu_utilisation(eng.nodes) * 100
    st.session_state.cpu_history.append(current_cpu)

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

# --- Calculate memory utilisation ---
total_mem_capacity = sum(n.mem_capacity for n in eng.nodes)
total_mem_used = sum(n.mem_used for n in eng.nodes)

if total_mem_capacity > 0:
    avg_mem = total_mem_used / total_mem_capacity
else:
    avg_mem = 0

util_df = pd.DataFrame({
    "Resource": ["CPU", "Memory"],
    "Used %": [
        round(avg_cpu * 100, 1),
        round(avg_mem * 100, 1)
    ]
})

fig = px.bar(
    util_df,
    x="Used %",
    y="Resource",
    orientation="h",
    range_x=[0, 100],
    text="Used %",
    title="Overall Resource Usage"
)

fig.update_layout(height=300)

st.plotly_chart(fig, use_container_width=True)

st.info("Autoscaler scales out when average CPU utilisation is higher than the configured threshold.")

# --- CPU usage over time ---
st.subheader("CPU Usage Over Time")

if st.session_state.cpu_history:

    cpu_history_df = pd.DataFrame({
        "Tick": list(range(1, len(st.session_state.cpu_history) + 1)),
        "CPU Usage %": st.session_state.cpu_history
    })

    fig_cpu_history = px.line(
        cpu_history_df,
        x="Tick",
        y="CPU Usage %",
        markers=True,
        title="CPU Usage Over Simulation Ticks",
        range_y=[0, 100]
    )

    threshold = eng.autoscaler.cpu_threshold * 100

    fig_cpu_history.add_hline(
        y=threshold,
        line_dash="dash",
        line_color="red",
        annotation_text="Autoscale Threshold",
        annotation_position="top left"
    )

    fig_cpu_history.update_layout(height=350)

    st.plotly_chart(fig_cpu_history, use_container_width=True)

else:
    st.info("Click 'Tick (advance simulation)' to start recording CPU usage over time.")

# --- Topology view ---
st.subheader("Cluster Topology: Pods Nested Within Nodes")

def status_badge(text: str, ok: bool) -> str:
    bg = "#2ecc71" if ok else "#e74c3c"
    return f"<span style='background:{bg}; color:white; padding:4px 10px; border-radius:12px; font-size:12px; font-weight:600;'>{text}</span>"

node_cols = st.columns(max(1, min(3, len(eng.nodes))))

for idx, node in enumerate(eng.nodes):
    with node_cols[idx % len(node_cols)]:

        node_ok = node.status == NodeStatus.READY

        st.markdown(
            f"""
<div style="background-color:#F8FAFC; border:1px solid #DDE5EF; border-radius:16px; padding:18px; margin-bottom:18px; box-shadow:0 2px 8px rgba(0,0,0,0.05);">

<h3 style="margin-bottom:6px;"> {node.node_id}</h3>

<p>{status_badge(node.status.value, node_ok)}</p>

<p><b>CPU:</b> {node.cpu_used}/{node.cpu_capacity}</p>
<p><b>Memory:</b> {node.mem_used}/{node.mem_capacity}</p>

<hr style="border:0; border-top:1px solid #E1E7EF;">

<p><b>Pods scheduled on this node:</b></p>
</div>
""",
            unsafe_allow_html=True
        )

        if not node.pods:
            st.markdown(
                """
<div style="background-color:white; border:1px dashed #CBD5E1; border-radius:10px; padding:10px; color:#64748B; font-size:14px;">
No pods assigned
</div>
""",
                unsafe_allow_html=True
            )

        for p in node.pods:
            p_ok = p.status == PodStatus.RUNNING
            owner = getattr(p, "owner_name", None)
            owner_text = f"Deployment/{owner}" if owner else "Standalone Pod"
            pod_border = "#2ecc71" if p_ok else "#e74c3c"

            st.markdown(
                f"""
<div style="background-color:white; border-left:6px solid {pod_border}; border-radius:10px; padding:12px; margin:8px 0; box-shadow:0 1px 4px rgba(0,0,0,0.04);">
<b> {p.pod_id}</b><br>
{status_badge(p.status.value, p_ok)}<br><br>
<small>CPU: {p.cpu_req} | Memory: {p.mem_req} | Owner: {owner_text}</small>
</div>
""",
                unsafe_allow_html=True
            )

        

# --- Pending pods ---
pending = [p for p in eng.pods if p.status == PodStatus.PENDING]
failed = [p for p in eng.pods if p.status == PodStatus.FAILED]

col_pending, col_failed = st.columns(2)


# Pending Pods

with col_pending:

    st.subheader("Pending Pods")

    if not pending:

        st.markdown(
            """
<div style="
background-color:#FFF7ED;
border:1px dashed #F59E0B;
border-radius:12px;
padding:12px;
color:#92400E;
">
No pending pods
</div>
""",
            unsafe_allow_html=True
        )

    for p in pending:

        owner = getattr(p, "owner_name", None)
        owner_text = f"Deployment/{owner}" if owner else "Standalone Pod"

        st.markdown(
            f"""
<div style="
background-color:#FFFBEB;
border-left:6px solid #F59E0B;
border-radius:12px;
padding:14px;
margin-bottom:10px;
box-shadow:0 1px 4px rgba(0,0,0,0.05);
">

<b> {p.pod_id}</b><br>

<span style="
background:#F59E0B;
color:white;
padding:3px 8px;
border-radius:10px;
font-size:12px;
font-weight:600;
">
PENDING
</span>

<br><br>

<small>
CPU: {p.cpu_req} |
Memory: {p.mem_req} |
Owner: {owner_text}
</small>

</div>
""",
            unsafe_allow_html=True
        )

# Failed Pods

with col_failed:

    st.subheader("Failed Pods")

    if not failed:

        st.markdown(
            """
<div style="
background-color:#FEF2F2;
border:1px dashed #DC2626;
border-radius:12px;
padding:12px;
color:#991B1B;
">
No failed pods
</div>
""",
            unsafe_allow_html=True
        )

    for p in failed:

        st.markdown(
            f"""
<div style="
background-color:#FEF2F2;
border-left:6px solid #DC2626;
border-radius:12px;
padding:14px;
margin-bottom:10px;
box-shadow:0 1px 4px rgba(0,0,0,0.05);
">

<b> {p.pod_id}</b><br>

<span style="
background:#DC2626;
color:white;
padding:3px 8px;
border-radius:10px;
font-size:12px;
font-weight:600;
">
FAILED
</span>

</div>
""",
            unsafe_allow_html=True
        )

st.subheader("Simulation Event Timeline")

log_df = eng.logger.to_dataframe()

if not log_df.empty:
    timeline_df = log_df.copy()
    timeline_df["step"] = range(1, len(timeline_df) + 1)

    fig_timeline = px.scatter(
        timeline_df,
        x="step",
        y="type",
        title="Cluster Events Over Simulation Time",
        hover_data=timeline_df.columns,
    )

    fig_timeline.update_layout(height=350)
    st.plotly_chart(fig_timeline, use_container_width=True)
else:
    st.info("No events recorded yet.")

# --- Logs + export ---
with st.expander("Event Log", expanded=False):
    df = eng.logger.to_dataframe()
    st.dataframe(df, use_container_width=True)

if st.button("Export CSV"):
    path = "simulation_log.csv"
    eng.logger.export_csv(path)
    st.success("Exported simulation_log.csv (saved in project folder).")

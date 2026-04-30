# Kubernetes Cluster Simulator

## Project Title
Designing and Implementing a Simulation of a Kubernetes Cluster to Visualise and Analyse Key Orchestration Concepts

---

## Project Overview

This project presents an interactive simulation of a Kubernetes cluster developed using Python and Streamlit.  
The simulator models core container orchestration behaviours such as scheduling, autoscaling, deployment management, and fault tolerance.  

The system provides a visual and educational representation of how Kubernetes components interact to manage workloads in a distributed system.

Users can:

- Create pods and deployments
- Configure resource requirements
- Submit workloads using templates
- Deploy workloads from YAML configuration files
- Simulate node and pod failures
- Observe autoscaling behaviour
- Monitor resource utilisation
- Visualise cluster topology and events

The simulator is designed as both:

- an educational tool
- a system analysis platform
- a distributed systems demonstration

---

## Running the Kubernetes Cluster Simulator

To run the Kubernetes Cluster Simulator locally, follow these steps:

1. Clone the GitHub repository:

git clone https://github.com/your-username/k8s-simulator.git

2. Navigate to the project directory:

cd k8s-simulator

3. Create and activate a virtual environment:

python3 -m venv .venv
source .venv/bin/activate

4. Install dependencies:

pip install -r requirements.txt

5. Set the Python path:

export PYTHONPATH=src

6. Run the application:

streamlit run src/ui/app.py

## Key Features

### Workload Creation Template

Users can create workloads using an interactive form that allows configuration of:

- Workload type (Pod or Deployment)
- CPU request
- Memory request
- Number of replicas
- Workload name

This template allows flexible workload creation similar to Kubernetes deployment configuration.

---

### YAML Deployment Support

The simulator allows users to deploy workloads using YAML configuration files.

Example:

```yaml
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  resources:
    cpu: 2
    memory: 2
```

### Scheduling Algorithms

The simulator supports multiple scheduling strategies:

- Round Robin Scheduling
- Bin Packing Scheduling

These algorithms determine how pods are assigned to nodes based on available resources.

---

### Autoscaling

The autoscaler monitors CPU utilisation across nodes and automatically adds new nodes when utilisation exceeds a defined threshold.

This simulates:

Horizontal scaling in Kubernetes clusters.

---

### Fault Injection

Users can simulate system failures including:

- Node crash
- Pod failure

The system demonstrates:

Self-healing behaviour through deployment reconciliation.

When a pod fails, the controller automatically creates a replacement pod to maintain the desired number of replicas.

---

### Cluster Topology Visualisation

The simulator displays a visual representation of the cluster showing:

- Nodes
- Running pods
- Resource usage
- Pod ownership
- Node status

This allows users to observe workload distribution across the cluster.

---

### Resource Utilisation Monitoring

The system provides graphical visualisation of resource consumption including:

- CPU utilisation
- Memory utilisation
- Resource usage over time

These diagrams help analyse system performance and cluster behaviour.

---

### Event Logging

All system events are recorded and displayed, including:

- Pod creation
- Deployment creation
- Scheduling decisions
- Node scaling
- Pod failures
- Recovery actions

Logs can be exported as a CSV file for further analysis.

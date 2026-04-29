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

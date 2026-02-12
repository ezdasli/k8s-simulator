Kubernetes Cluster Simulator
Final Year Project – University of Westminster

Project Title
Designing and Implementing a Simulation of a Kubernetes Cluster to Visualise and Analyse Key Orchestration Concepts

Overview
This project is an interactive educational simulator that models the internal behaviour of a Kubernetes cluster.
Instead of requiring access to a live cloud infrastructure, the system provides a controlled, visual simulation environment where users can observe and analyse:
* Pod scheduling decisions
* Resource allocation
* Autoscaling behaviour
* Node failures and recovery
* Cluster performance metrics
The simulator is designed to support learning in distributed systems and cloud computing.

Objectives
The primary objectives of this project are:
* Simulate Kubernetes scheduling logic
* Model autoscaling behaviour based on CPU utilisation
* Demonstrate fault tolerance and recovery
* Provide real-time cluster visualisation
* Log orchestration events for analysis

System Architecture
The project follows a modular object-oriented design:

models.py       → Core entities (Pod, Node)
scheduler.py    → Scheduling logic
autoscaler.py   → Cluster autoscaling behaviour
controller.py   → Failure detection and recovery
engine.py       → Simulation loop controller
logging.py      → Event logging and metrics tracking
app.py          → Streamlit UI interface

This modular architecture ensures:
* Maintainability
* Extensibility
* Clear separation of concerns

Features Implemented
Scheduler Simulation
* Assigns Pods to Nodes
* Respects CPU and memory constraints
* Real-time placement visualisation

Autoscaler Simulation
* Monitors average CPU utilisation
* Adds new nodes when threshold is exceeded (e.g., >80%)

Fault Injection
* Manual Node failure injection
* Controller-based recovery logic
* Pod rescheduling to healthy nodes

Real-Time Visualisation
* Cluster topology display
* Pods nested inside Nodes
* Colour-coded status indicators

Logging & Metrics
* Scheduling decisions logged
* Autoscaling events recorded
* Failure and recovery events tracked
* Export capability for further analysis

Technologies Used
* Python 3
* Streamlit (UI)
* Object-Oriented Programming
* Simulation modelling
* CSV logging for metrics export

How to Run the Project

Clone the Repository
git clone https://github.com/yourusername/k8s-simulator.git
cd k8s-simulator

Create Virtual Environment
python -m venv .venv
source .venv/bin/activate  # Mac/Linux

Install Dependencies
pip install -r requirements.txt

Run the Application
PYTHONPATH=src streamlit run src/ui/app.py

The simulator will open in your browser.

Demonstration Capabilities
The simulator allows users to:
1. Create Pods with configurable CPU & memory requirements
2. Advance the simulation using Tick
3. Observe scheduling decisions
4. Increase workload to trigger autoscaling
5. Manually inject Node failures
6. Observe controller-driven recovery

Example Use Case
* Create multiple pods
* Increase CPU demand
* Observe autoscaler create new nodes
* Inject a node crash
* Watch pods reschedule automatically
This demonstrates Kubernetes-style self-healing behaviour.

Academic Context
This project was developed as part of a Final Year BSc Computer Science at the University of Westminster.
It addresses the pedagogical gap in teaching Kubernetes orchestration by providing an interactive simulation tool rather than relying on live clusters.

Future Improvements
* Improved dashboard visualisation
* Advanced scheduling algorithms (e.g., bin-packing)
* Config save/load via JSON
* More detailed performance analytics
* Deployment scenario simulation

Author
Ezgi Damla Asli
BSc Computer Science
University of Westminster
Supervisor: Hamed Hamzeh

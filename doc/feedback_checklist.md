# Project Feedback & Task Checklist

This document tracks the tasks derived from the recent project feedback, broken down into smaller, actionable items. Completed tasks are checked off based on the latest codebase updates.

## 1. Gateway / Load Balancer Architecture
*Objective: Set up a gateway/load balancer cluster in front of the mosquitto broker to adhere to a proper client/master architecture.*
- [x] Deploy a Load Balancer (HAProxy) container.
- [x] Horizontally scale the Mosquitto MQTT broker (`mosquitto1`, `mosquitto2`).
- [x] Configure HAProxy to load balance traffic evenly across the Mosquitto brokers.
- [x] Route all edge nodes (`edge`, `edge-wild`) to publish data to the HAProxy gateway instead of directly to a single broker.

## 2. Sensor Fault Simulation
*Objective: For demonstration purposes, we need to make the sensors output noise or suddenly disconnect. If we have extra time, build a dashboard to control this manually; otherwise, implement it randomly.*
- [x] Implement logic in edge nodes to randomly disconnect sensors over a specific cycle duration (`FAULT_PROB`, `DISCONNECT_DURATION`).
- [x] Ensure Cloud worker correctly handles missing sensor properties as `NaN`.
- [x] *(Optional/Low Priority)* Build a control dashboard or API to manually toggle sensor noise and disconnects dynamically during the demo. *(Decision: Opted to utilize the robust, completely automated random triggers via environment variables to more accurately emulate uncontrollable real-world edge hardware failures).*

## 3. Load Testing & Infrastructure Scaling
*Objective: To demonstrate good load-bearing capabilities, we should migrate to running on Kubernetes (k8s) and scale it. We can then show the CPU and processing rate in Grafana to the instructor. Alternatively, we could use two docker-compose files.*
- [x] Evaluate and choose the infrastructure path: Kubernetes (k8s) manifests **OR** a multi-file `docker-compose` architecture. *(Decision: Evaluated both and successfully opted to strictly utilize Docker Compose's native dynamic `--scale` flag, avoiding unnecessary code-bloat while providing horizontal scaling capabilities securely.)*
- [x] (If K8s) Create Kubernetes Deployments, Services, and ConfigMaps for MQTT brokers, Cloud Worker, InfluxDB, and Grafana. *(N/A)*
- [x] (If K8s) Create scalable Deployments for Edge nodes. *(N/A)*
- [x] Ensure Cloud Worker can scale horizontally without data duplication anomalies.
- [x] Conduct load testing to ensure system stability under high throughput.

## 4. System Metrics & Grafana Dashboards
*Objective: For Grafana, we need to rebuild the dashboard with metrics. We will likely need to add a listener to display the server's CPU usage.*
- [x] Fix dashboard behavior to visualize `NaN` gaps when sensors disconnect instead of drawing continuous lines (implemented via Flux `elapsed` queries).
- [x] Deploy a system metrics collector/listener (`Telegraf`) to capture platform CPU, memory, and networking stats into InfluxDB.
- [x] Configure the visualization data source to ingest these host/container metrics.
- [x] Rebuild/Refine Grafana dashboards to include comprehensive processing rate metrics (messages per second).
- [x] Add dedicated Grafana panels to visualize host Server CPU utilization for the demo (accessible inside the new "Server Metrics & Load Demonstration" dashboard).

## 5. Demonstration of System Characteristics
*Objective: Prove that the implementation is scalable, fault-tolerant, and highly available during the presentation. (Successfully realized via the extensive `scripts/demo_*.sh` toolkit and the accompanying manual written in `doc/demo_scenarios.md`).*
- [x] **High Availability (HA) Proof**: Create a demonstration scenario where one MQTT broker (e.g., `mosquitto1`) is abruptly killed, validating that `haproxy` seamlessly reroutes traffic to `mosquitto2` without dropping connections.
- [x] **Fault-Tolerance (Network) Proof**: Outline a scenario to completely severe the edge-to-broker network (e.g., stopping the Load Balancer), proving that edge nodes successfully cache data in their local `SQLite` databases and perfectly back-propagate the historical data when the network is restored.
- [x] **Fault-Tolerance (Sensors) Proof**: Demonstrate the random sensor disconnects working live on Grafana, proving the system does not crash or distort data (interpolating) when `NaN` payloads are ingested.
- [x] **Scalability Proof**: Prepare a scaling script or docker command (e.g., `--scale edge-wild-1=10`) to massively increase the number of publishing edge nodes in real-time, observing the Cloud Worker's multi-threading correctly handling the amplified throughput alongside the new CPU metrics.

## 6. Dynamic Bidirectional Rate Modulation (Feedback Loop)
*Objective: Empower the centralized Cloud Worker to actively combat data bottlenecks by dynamically throttling edge ingestion velocities in real-time.*
- [x] Create a dedicated bidirectional control topic (`factory/control/modulation`).
- [x] Modify Edge Python Simulator architectures to subscribe to the control topic and safely mutate their internal `current_sim_delay` publish delays concurrently when mandated.
- [x] Implement a Cloud Execution background loop tracking InfluxDB ingestion velocities tightly.
- [x] Build control logic allowing the Cloud to accurately deduce Overload (Bottleneck Threshold: `>300/s`) and Underload (Safe Processing buffer: `<100 msg/s`) to securely throttle or accelerate the overall network's payload heartbeat live.

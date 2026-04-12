# 🎬 Final Presentation Demo Guide

This guide provides a structured, step-by-step roadmap to present your Edge Computing architecture seamlessly, allowing you to definitively prove every technical claim to your audience.

---

## Step 1: Initializing the Environment
Start with a clean slate to prove the system initializes gracefully.

1. Open a terminal in the root of the project.
2. Run the cleanup and reinitialization script (this aggressively purges old databases and spins up fresh container clusters):
   ```bash
   ./scripts/reinitialize_all.sh
   ```
3. Wait roughly 10 seconds for `InfluxDB` to provision internally and the `Cloud Worker` to establish its threaded connections to the Load Balancer.

---

## Step 2: Showcasing Application Operations
Navigate your browser to the Grafana interface: **[http://localhost:3000](http://localhost:3000)** (Login: `admin` / `admin`).

Walk the professor through the active dashboards to orient them:
- **Fleet Health Overview**: Point out that all 8 edge units (4 NASA historical datasets, 4 autonomous wildcards) are actively inserting telemetry concurrently.
- **Server Metrics & Load Demonstration**: Show that the Telegraf monitoring daemon is actively providing Host CPU metrics and that the message processing rate is stable.

---

## Step 3: Proving Fault-Tolerance (Sensor Hardware Decay)
Open the **All-Sensor Deep Dive** dashboard.

1. Target a specific engine unit in the dropdown.
2. Point the audience to the absolute "gaps" in the plotted sensor lines (if none appear immediately, wait a few seconds or switch units as the fault-probability triggers dynamically).
3. Explain that this acts as proof for **Payload Resilience**: The edge simulation is designed to randomly disconnect noisy sensors (`FAULT_PROB`). Our Cloud Worker gracefully handles these `None` arrays, persisting them as `NaN`. Most importantly, our Grafana layer utilizes the Flux `elapsed()` function to display missing links correctly rather than drawing misleading, interpolated regression lines over dead hardware signals.

---

## Step 4: Proving High Availability (Broker Cluster Failover)
Demonstrate that the custom **HAProxy Load Balancer** architecture protects against monolithic failure.

1. Bring up your terminal.
2. Abruptly kill the primary Mosquitto Master node:
   ```bash
   ./scripts/demo_ha_trigger.sh
   ```
3. Show the Grafana dashboard. It will not freeze. Expalin that HAProxy detected the death via internal `tcp-check` and instantly rerouted all publishers and subscribers entirely to `mosquitto2`. The system successfully survives.
4. Spin the broken node back up:
   ```bash
   ./scripts/demo_ha_revert.sh
   ```

---

## Step 5: Proving Edge Node Persistence (Network Outages)
Demonstrate what happens when an edge node loses all internet connectivity to the Cloud.

1. Simulate a catastrophic gateway failure by bringing down the entire Load Balancer:
   ```bash
   ./scripts/demo_network_trigger.sh
   ```
2. Wait 30 to 60 seconds. Explain that the edge nodes are entirely locked out of the Cloud. However, instead of discarding the telemetry, they are systematically writing compressed payloads into local `SQLite` buffer databases (Offline Mode).
3. Prove it by showing the server ingestion rate in Grafana dropping completely to zero.
4. Restore the network connection securely:
   ```bash
   ./scripts/demo_network_revert.sh
   ```
5. Look back at Grafana. The ingestion rate will instantly spike vertically as the edge nodes automatically realize the connection is restored and aggressively flush their entire local `SQLite` caches. Concrete proof of zero data payload loss!

---

## Step 6: Proving Scalability under Heavy Ingestion
Return to the **Server Metrics & Load Demonstration** dashboard.

1. Inform the professor that you will now severely overload the ingestion network by cloning the edge simulators horizontally on the fly.
2. Execute the scale-up script:
   ```bash
   ./scripts/demo_scale_trigger.sh
   ```
   *(This Docker command launches 12 brand new autonomous simulators instantly).*
3. Observe the Grafana charts. The **Host CPU Usage** will distribute dynamically, and the **Messages Processed Per Second** will climb rapidly. Explain that the Python multi-threaded Cloud Worker cleanly scales its resource consumption.
4. **Demonstrate Autonomous Rate Modulation (Feedback Loop)**:
   - While the network is heavily loaded, switch to the Cloud Worker logs (`docker logs --tail 20 -f cloud-worker`).
   - Show the audience that once ingestion crosses the 300 msg/sec threshold, the server actively broadcasts a throttle payload over the `factory/control/modulation` MQTT topic.
   - Switch to the edge logs (`docker logs --tail 20 -f edge-node-1`). You will see it intercept the command and print `🚦 [MODULATION] Server commanded delay change`, physically locking its execution to throttle the pipeline.
   - Show the Grafana charts naturally plateauing rather than bottlenecking and eventually falling when the nodes speed back up, proving the system autonomously mitigates distributed DDoS-level loads! 
5. Conclude the demonstration by gracefully scaling down the network back to baseline: 
   ```bash
   ./scripts/demo_scale_revert.sh
   ```

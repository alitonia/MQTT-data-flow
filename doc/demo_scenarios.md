# Demonstration Scenarios

This document outlines the step-by-step interactive scenarios to execute during your presentation to definitively prove the system is **High Available**, **Fault-Tolerant**, and **Scalable**.

---

## 1. Proving High Availability (HA)
*Goal: Show that if a vital messaging component dies, the system stays online without interruption.*

**The Setup:**
1. Open the Real-Time Grafana dashboard showing active sensor ingestion.
2. Ensure both `mosquitto1` and `mosquitto2` are running.
3. Show the audience the dual-broker architecture diagram.

**The Action:**
Abruptly kill the first broker:
```bash
docker stop mosquitto1
```

**The Proof:**
- **Observe Edge Nodes:** The edge nodes will briefly lose connection but will instantly reconnect entirely to `mosquitto2` seamlessly via the HAProxy Load Balancer. 
- **Observe Grafana:** The data stream will continue uninterrupted after a momentary sub-second stutter. No data payload is permanently lost.
- **Cleanup:** `docker start mosquitto1`

---

## 2. Proving Fault-Tolerance (Network Loss & Persistence)
*Goal: Show that edge nodes can survive prolonged, complete network outages in "offline mode" without dropping data.*

**The Setup:**
1. Ensure the system is running smoothly. 

**The Action:**
Simulate a catastrophic gateway failure by stopping the entire Load Balancer:
```bash
docker stop mqtt-lb
```

Wait 30-60 seconds.

**The Expected Behavior:**
- Checking edge logs (`docker logs -f edge-node-1`), you will see errors stating `Disconnected from MQTT Broker!`.
- They will begin logging: `Buffered compressed batch...` indicating the SQLite offline persistence layer has activated.

**The Proof:**
Turn the gateway back on:
```bash
docker start mqtt-lb
```
- **Observe Edge Logs:** They will reconnect and print `Published buffered batch...` as they aggressively flush the SQLite cache to the broker.
- **Observe Grafana:** You will see an immediate vertical spike of ingested data perfectly backfilling the timeline where the offline gap occurred.

---

## 3. Proving Fault-Tolerance (Sensor Hardware Noise)
*Goal: Prove that unpredictable hardware sensor failures (producing `None`/`NaN`) are handled gracefully.*

**The Setup:**
1. Open the "All-Sensors Grid" Grafana dashboard for a specific engine.

**The Action/Proof:**
- Point out the random gaps in the sensor line graphs.
- Explain that we purposefully engineered the edge nodes to randomly output signal loss (`FAULT_PROB`).
- Highlight that the Cloud Worker does not crash when parsing `None` floats, and the flux `elapsed()` queries strictly respect these gaps as "Unknown/Failed" statuses rather than drawing fake, misleading interpolated regression lines between the healthy points.

---

## 4. Proving Scalability & Load Management
*Goal: Prove the infrastructure can elastically expand to handle a massive influx of new IoT devices.*

**The Setup:**
1. We will need the CPU / Metrics dashboard actively open in Grafana (currently on the To-Do list to be created).
2. Note the baseline processing rate and CPU load.

**The Action:**
Vastly multiply the number of simulators generating synthetics payloads:
```bash
docker-compose up -d --scale edge-wild-1=5 --scale edge-wild-2=5 --scale edge-wild-3=5
```
*(This inflates the network by adding 12 new aggressive edge nodes instantly)*

**The Proof:**
- **Observe Cloud Worker Logs:** The multi-threaded cloud consumer will immediately detect the immense influx of new traffic dynamically across all brokers.
- **Observe Grafana Metrics:** The CPU load will safely distribute. The "Messages Processed Per Second" metric will climb substantially but remain stable without OOM (Out of Memory) crashing.
- **Cleanup:** Scale them back down with `--scale edge-wild-*=1`.

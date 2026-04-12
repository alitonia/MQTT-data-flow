# Analysis of Latest Commits

This document provides an overview of the changes introduced in the recent commits (origin/hoangnn merged into main). The commits include major architecture improvements focusing on load balancing and simulated sensor faults.

## 1. Architectural Changes: High Availability & Load Balancing
- **HAProxy Load Balancer Introduced:** An HAProxy load balancer was added to serve as a gateway for the Edge nodes.
- **Multiple MQTT Brokers:** The single `mosquitto` broker in `docker-compose.yml` has been scaled horizontally. Now there are two brokers, `mosquitto1` and `mosquitto2`.
- **Connections routing:** All Edge components (both `edge` and `edge-wild` containers) are now configured to publish topic data to the `haproxy` LB rather than a single mosquitto broker directly.

## 2. Cloud Worker Enhancements
- **Multi-Broker Threading:** `cloud/main.py` was refactored to spawn a separate MQTT client thread for each available broker (as specified by `MQTT_BROKERS`).
- **Connection Reliability:** The client script now handles connecting to multiple brokers reliably, ensuring that the InfluxDB persistence layer gathers data dynamically from whatever backend nodes are available.
- **Null Value handling:** Retained and polished support for `NaN` handling when sensor data points are gracefully missing.

## 3. Edge Node (Fault Simulation)
- **Random Sensor Disconnects:** To test system resilience and behavior under failure, `edge/main.py` incorporates a random fault trigger. 
  - Controlled via `FAULT_PROB` (default: 10% chance) and `DISCONNECT_DURATION` (default: 15 cycles).
  - When triggered, a pseudo-random sensor's value will drop out (become `None`) for the specific duration and then recover automatically.
- **Logging Improvements:** Added informative tagging (`[FAULT]` and `[RECOVER]`) to stdout to trace the behavior of disconnecting sensors.

## 4. Grafana Dashboards Updates
- **Gap Detection:** Modified the Flux queries in `grafana/provisioning/dashboards/all_sensors_grid.json`. 
- **Elapsed Time Handling:** Instead of drawing continuous lines during sensor disconnections or missing data, the dashboard now uses the `elapsed()` function. If the gap between data points exceeds 1500ms, the query maps the value to `NaN` (float `0.0/0.0`), properly visualizing sensor dropout events.

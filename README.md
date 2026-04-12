# Hybrid Edge-Cloud Integration for IoT Ecosystems

This project implements a tiered IoT architecture that optimizes computational load between **Edge devices** and a **Central Cloud**. It uses the **NASA Turbofan Engine Degradation Dataset** as a real-world telemetry source to simulate industrial sensor networks.

## 🚀 Key Features
- **Lightweight Protocol**: MQTT (Mosquitto) for efficient device-to-cloud communication.
- **High Availability**: Custom HAProxy instance load balancing traffic evenly across a scaled Mosquitto broker cluster.
- **Resilience Testing**: Engineered random edge sensor fault simulations to test overall systemic ingestion reliability.
- **Edge Pre-processing**: Filtering/compression (zlib) to save bandwidth.
- **Data Synchronization**: Local SQLite buffering to handle intermittent network connectivity.
- **Massive Scalability**: Orchestrates 8 parallel edge nodes (4 real-data, 4 autonomous generators).
- **Time-Series Deep Dive**: InfluxDB for data storage and Grafana for multi-dashboard visualization.
- **High Fidelity**: Nanosecond precision timestamps for accurate sequence preservation.

## 🏗 Architecture
1. **Edge Nodes (Python)**:
   - Read NASA dataset or generate synthetic "Wildcard" telemetry.
   - Simulate random sensor noise/disconnect events for resilience testing.
   - Filter out small fluctuations to intelligently reduce traffic.
   - Batch and compress data using zlib before publishing.
   - Store payload locally in SQLite if the gateway is unreachable.
2. **Gateway / Load Balancer (HAProxy)**: Serves as the primary entry point proxy, routing traffic across multiple brokers.
3. **MQTT Broker Cluster (Eclipse Mosquitto)**: Horizontally scaled brokers (`mosquitto1`, `mosquitto2`) to form a highly-available messaging backbone.
4. **Cloud Worker (Python)**: Utilizes multi-threading to concurrently subscribe to the entire broker cluster, decompresses incoming data, gracefully handles faulty properties (NaN), and performs batch writes to InfluxDB.
5. **Time-Series Database (InfluxDB 2.7)**: Highly efficient storage for millions of sensor points.
6. **Visualization (Grafana)**: Pre-provisioned dashboards equipped with advanced Flux queries to visualize gaps when sensors disconnect.

## 🛠 Getting Started

### Prerequisites
- Docker & Docker Compose
- The NASA dataset in the `archive-NASA C-MAPSS-1 Turbofan Engine Degradation Dataset/` directory.

### Launching the Simulation
Run the master reinitialization script to clear any previous state and build the latest images:
```bash
./scripts/reinitialize_all.sh
```
*Alternatively:* `docker-compose up -d --build`

### Accessing the Dashboard
- **URL**: [http://localhost:3000](http://localhost:3000)
- **Username**: `admin`
- **Password**: `admin`

## 🎬 Presentation Demo Scripts
For executing live proofs of architectural characteristics during demonstrations, dedicated trigger and revert scripts have been created in the `scripts/` directory:

1. **High Availability (HA)**: Sever a master broker node and observe the system naturally failover.
   - Run: `./scripts/demo_ha_trigger.sh` / Revert: `./scripts/demo_ha_revert.sh`
2. **Network Fault-Tolerance**: Sever the Load Balancer gateway enforcing prolonged offline persistence caching.
   - Run: `./scripts/demo_network_trigger.sh` / Revert: `./scripts/demo_network_revert.sh`
3. **Sensor Noise Testing**: Demonstrate payload failures.
   - *(Note: `./scripts/demo_sensor_*.sh` are currently placeholders awaiting API implementation. Noise continues to trigger automatically at 10% randomly for now.)*
4. **Traffic Scalability**: Massively simulate parallel sensor nodes to overload processing.
   - Run: `./scripts/demo_scale_trigger.sh` / Revert: `./scripts/demo_scale_revert.sh`

## 📊 Available Dashboards
1. **Fleet Health Overview**: High-level monitor of all 8 nodes and active engine unit counts.
2. **All-Sensor Deep Dive**: Detailed engineering view of all 21 sensor channels for any specific engine unit.
3. **Real-Time Simulation**: DevOps view of ingestion cycles and edge-node progress.
4. **Server Metrics & Load Demonstration**: Live hardware monitoring of Host CPU Usage provided by Telegraf, mapped alongside Cloud Worker message processing rates for accurately benchmarking performance under heavy loads.

## 📂 Project Structure
- `edge/`: Core edge logic for NASA dataset simulation.
- `edge-wild/`: Autonomous synthetic data generator.
- `cloud/`: Cloud worker for message ingestion.
- `grafana/`: Provisioning files (dashboards, data sources).
- `mosquitto/`: Broker configuration.
- `telegraf/`: System metric interception configuration for robust Server observability.
- `scripts/`: Operational toolkits spanning infrastructure resets, database purging, and interactive demonstration scenarios.

## 🧹 Maintenance
To purge all historical data (InfluxDB volumes, SQLite buffers, Grafana state) without restarting:
```bash
./scripts/clean_data.sh
```
# MQTT-data-flow

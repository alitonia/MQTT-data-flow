# Hybrid Edge-Cloud Integration for IoT Ecosystems

This project implements a tiered IoT architecture that optimizes computational load between **Edge devices** and a **Central Cloud**. It uses the **NASA Turbofan Engine Degradation Dataset** as a real-world telemetry source to simulate industrial sensor networks.

## 🚀 Key Features
- **Lightweight Protocol**: MQTT (Mosquitto) for efficient device-to-cloud communication.
- **Edge Pre-processing**: Filtering/compression (zlib) to save bandwidth.
- **Data Synchronization**: Local SQLite buffering to handle intermittent network connectivity.
- **Massive Scalability**: Orchestrates 8 parallel edge nodes (4 real-data, 4 autonomous generators).
- **Time-Series Deep Dive**: InfluxDB for data storage and Grafana for multi-dashboard visualization.
- **High Fidelity**: Nanosecond precision timestamps for accurate sequence preservation.

## 🏗 Architecture
1. **Edge Nodes (Python)**:
   - Read NASA dataset or generate synthetic "Wildcard" telemetry.
   - Filter small fluctuations to reduce traffic.
   - Batch and compress data using zlib.
   - Store locally if the MQTT broker is unreachable.
2. **MQTT Broker (Eclipse Mosquitto)**: Lightweight message backbone.
3. **Cloud Worker (Python)**: Subscribes to events, decompresses data, and performs batch writes to InfluxDB.
4. **Time-Series Database (InfluxDB 2.7)**: Highly efficient storage for millions of sensor points.
5. **Visualization (Grafana)**: Pre-provisioned dashboards for fleet monitoring.

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

## 📊 Available Dashboards
1. **Fleet Health Overview**: High-level monitor of all 8 nodes and active engine unit counts.
2. **All-Sensor Deep Dive**: Detailed engineering view of all 21 sensor channels for any specific engine unit.
3. **Real-Time Simulation**: DevOps view of ingestion cycles and edge-node progress.

## 📂 Project Structure
- `edge/`: Core edge logic for NASA dataset simulation.
- `edge-wild/`: Autonomous synthetic data generator.
- `cloud/`: Cloud worker for message ingestion.
- `grafana/`: Provisioning files (dashboards, data sources).
- `mosquitto/`: Broker configuration.
- `scripts/`: Utility scripts for data purging and environment resetting.

## 🧹 Maintenance
To purge all historical data (InfluxDB volumes, SQLite buffers, Grafana state) without restarting:
```bash
./scripts/clean_data.sh
```
# MQTT-data-flow

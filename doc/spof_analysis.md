# Single Points of Failure (SPOF) Analysis

## Overview
While the architecture successfully utilizes horizontally scaled MQTT brokers (the Mosquitto Cluster) and physically distributed, autonomous edge nodes to eliminate mid-tier bottlenecks, the pipeline currently contains four structural Single Points of Failure (SPOF) commonly found in centralized IoT infrastructure pipelines.

---

## 1. The Gateway Entry Point (`HAProxy`)
**Vulnerability:** All edge telemetry funnels into a single load-balancer container (`mqtt-lb`) mapped to port `1883`. If this instance experiences a segmentation fault, OOM error, or dedicated host hardware failure, the entire edge device network is abruptly severed from the downstream brokers. Offline caches will activate, but live ingestion halts globally.

**Update Plan:** Deploy a secondary HAProxy array and govern both balancers using a daemon like `Keepalived` over a Virtual IP (VIP).
* **Pros:** Establishes true gateway high-availability. Failovers occur in milliseconds natively at the kernel routing layer without requiring any IP changes on the client Edge node configurations.
* **Cons:** High network configuration complexity. Requires deploying VRRP broadcast protocols which frequently conflict natively with virtualized Docker bridge environments or certain major Cloud provider VPCs.

---

## 2. Ingestion Pipeline (`Cloud Worker Daemon`)
**Vulnerability:** Telemetry routing relies on a solitary Python ingestion microservice bridging the Mosquitto queues and the database. If the script crashes entirely due to an unhandled OS exception, raw telemetry will build up infinitely in Mosquitto queues until physical memory limits are exhausted.

**Update Plan:** Migrate the system to utilize MQTT version 5 **Shared Subscriptions** (e.g., `$share/ingest_cluster/factory/data`). Spin up multiple replicas of the Cloud Worker container simultaneously.
* **Pros:** Effortlessly scales the cloud ingestion horizontally. If one worker process shuts down, sibling replicas natively absorb the stranded messages, preventing pipeline locking indefinitely.
* **Cons:** Requires upgrading Paho/Eclipse stacks strictly to MQTT v5, which may break older legacy Edge simulation clients. Furthermore, shared subscriptions frequently induce message ordering disarrangement, requiring aggressive mathematical index/timestamp sorting directly at the UI layer.

---

## 3. Persistence Backbone (`InfluxDB 2.7`)
**Vulnerability:** Deep time-series histories converge onto a single open-source InfluxDB persistence container. If the foundational database volume corrupts, locks, or runs out of inodes, all Cloud Workers identically fail to execute insertion routines, dropping payload cascades entirely.

**Update Plan:** Completely migrate away from single-node deployments to natively clustered database environments (e.g., InfluxDB Enterprise, Apache Cassandra, or a managed cloud-native suite like AWS Timestream).
* **Pros:** Total localized data redundancy and data longevity. Provides the capability to scale payload insertion thresholds massively without bottlenecking on a single SSD I/O limitation limit.
* **Cons:** Exorbitantly high operational overhead. Clusters significantly complicate standard snapshot practices, restore procedures, and backup persistence compared to a simple docker bind-mount.

---

## 4. Operational Observability (`Grafana`)
**Vulnerability:** The central system UI depends on a solitary Grafana dashboard node. While a crash here physically doesn't halt IoT payload ingestion (the pipeline continues behind the scenes), it completely blinds systems operators to the edge status.

**Update Plan:** Deploy multiple Grafana containers clustered natively behind the HAProxy load balancer, backed by a persistent high-availability Postgres SQL state-database to share user sessions seamlessly.
* **Pros:** Operators maintain 100% uninterrupted optical visibility into the IoT fleet gracefully, even during primary rendering node crashes.
* **Cons:** Severe architectural over-engineering. Because Grafana is primarily stateless and possesses nearly instant native reboot recovery speeds, requiring dedicated SQL state configurations yields incredibly marginal ROI for experimental lab networks.

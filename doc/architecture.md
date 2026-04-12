# Edge Computing IoT: System Architecture

The Edge Computing IoT platform utilizes a multi-tier, vertically integrated architecture designed to mimic a real-world enterprise deployment. It prioritizes fault tolerance, data compression, high concurrency, and precise storage explicitly tailored for time-series telemetry.

## Components Breakdown

### 1. Edge Layer (Producers / Sensors)
The edge layer consists of two parallel types of telemetry generators:
- **NASA Edge Nodes (`edge-node-1` to `edge-node-4`)**: Python applications that locally parse the NASA Turbofan Engine Degradation Dataset.
- **Autonomous Simulators (`edge-wild-1` to `edge-wild-4`)**: Synthetic actors that continuously create randomized telemetry data on the fly based on predetermined structures.

**Core Responsibilities:**
- **Filtration**: Pre-process raw data through small deviation filtering (prevents spamming brokers with completely unchanged states).
- **Compression**: Handle payload batching (every 10 data points) and aggressively compress strings into the `zlib` format before transmission.
- **Fault Simulation**: Emulate real-world hardware degradation: sensors will randomly drift and disconnect, resulting in `NaN` data properties over dynamically randomized operational cycles.
- **Offline Persistence**: Store payloads safely in local `SQLite` buffer/state files whenever network disruptions prevent external communication, publishing them sequentially upon reconnection.

### 2. Load Balancing Gateway 
All 8 downstream edge nodes are unified behind a central access point designed to prevent monolithic failures.
- **HAProxy (`mqtt-lb`)**: Listens prominently on port `1883` and acts as the singular entry point. Based on a `roundrobin` strategy, it receives, proxies, and evenly distributes publisher and subscriber workloads out to independent Mosquitto instances.

### 3. Pub/Sub Broker Cluster 
- **Mosquitto Nodes (`mosquitto1`, `mosquitto2`)**: Lightweight standard Eclipse Mosquitto instances. Deployed as a horizontally scaled array underneath the HAProxy gateway to radically alleviate request bottlenecking. 

### 4. Cloud Ingestion Layer (Consumer)
- **Cloud Worker (`cloud-worker`)**: A consolidated Python ingestion microservice bridging the gap between MQTT messaging and database writing.
  - Dynamically spawns discrete dedicated listener threads based on the cluster's size (`MQTT_BROKERS` env variables), allowing it to reliably capture traffic from the entirety of the split backend broker pool simultaneously.
  - **Dynamic Rate Moderator (Feedback Loop)**: Includes a background monitor tracking InfluxDB insertion thresholds. Whenever network throughput hits dangerous bottleneck speeds (>300 msg/sec), it publishes JSON payloads autonomously to a dedicated `factory/control/modulation` MQTT channel to securely command all edge nodes to throttle their publish cycles. When systems perform beneath 100 msg/sec, it identically commands them to accelerate, maximizing utilization securely.
  - Controls the reverse-data pipeline: unzips the `zlib` compressions and casts strings into JSON arrays.
  - Safely extracts the batch data and transforms it seamlessly into InfluxDB Line Protocol points (`Point("turbofan_telemetry")`), explicitly accounting for aforementioned hardware faults by translating empty inputs cleanly back to InfluxDB supported `NaN` floats.

### 5. Persistence & Visualization Layer
- **InfluxDB (`influxdb`)**: The central time-series historian. Engineered to handle thousands of concurrent queries without locks. Preserves the pure `nanosecond` precision originally stamped during edge data acquisition.
- **Grafana (`grafana`)**: A fleet surveillance dashboard. Operates atop InfluxDB utilizing specific dynamic Flux logic (the `elapsed()` function) to visibly alert analysts immediately to telemetry gaps/disconnects without interpolating fake sequential lines over gaps.

---

## Architectural Diagram

```mermaid
graph TD
    classDef edge fill:#e1f5fe,stroke:#03a9f4,stroke-width:2px;
    classDef gateway fill:#e0f2f1,stroke:#00897b,stroke-width:2px;
    classDef broker fill:#fff3e0,stroke:#ff9800,stroke-width:2px;
    classDef cloud fill:#e8f5e9,stroke:#4caf50,stroke-width:2px;
    classDef storage fill:#ede7f6,stroke:#673ab7,stroke-width:2px;

    subgraph Edge Operations Layer
        E1[Edge Node 1]:::edge
        E2[Edge Nodes 2-4]:::edge
        W1[Edge Wild 1]:::edge
        W2[Edge Wilds 2-4]:::edge
    end

    subgraph Load Balancer Layer
        HA[HAProxy Gateway<br>:1883]:::gateway
    end

    subgraph Distributed Broker Array
        M1[Mosquitto Node 1<br>:1884]:::broker
        M2[Mosquitto Node 2<br>:1885]:::broker
    end

    subgraph Cloud Operations Layer
        CW[Cloud Worker Core<br>Multi-threaded Pool]:::cloud
    end

    subgraph Data Analytics Layer
        DB[(InfluxDB 2.7)]:::storage
        GF[Grafana UI<br>:3000]:::storage
    end

    E1 -->|zlib batch MQTT publish| HA
    E2 -->|zlib batch MQTT publish| HA
    W1 -->|zlib batch MQTT publish| HA
    W2 -->|zlib batch MQTT publish| HA

    HA -->|TCP Round-Robin| M1
    HA -->|TCP Round-Robin| M2

    CW .->|Thread 1 subscribe| M1
    CW .->|Thread 2 subscribe| M2

    CW -->|Translates to Line Protocol| DB
    GF -->|Flux queries `elapsed()`| DB
    
    CW -.->|Feedback Rate Commands| HA
    HA -.->|Modulation Control Topic| E1
    HA -.->|Modulation Control Topic| E2
    HA -.->|Modulation Control Topic| W1
    HA -.->|Modulation Control Topic| W2
```

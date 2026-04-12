```text
===============================================================================================================
                                       EDGE COMPUTING IoT ARCHITECTURE
===============================================================================================================

  [ EDGE LAYER ]                                                          [ ANALYTICS & STORAGE LAYER ]
                                                                      
  +-----------------------+                                               +---------------------------+ 
  | Edge Simulators (x8)  |                                               | Grafana Dashboards        |
  | - NASA Dataset (x4)   |                                               | - Fleet Health            |
  | - Wildcard Synths (x4)|                                               | - Server Metrics          |
  |                       |                                               | - Flux `elapsed()` Viz    |
  | * Zlib Compressor     |                                               +-------------^-------------+
  | * SQLite Offline      |                                                             | Query Result
  | * Delta Deadbanding   |                                                             | 
  | * Payload Batching    |                                               +-------------+-------------+
  | * Signal Degradation  |                                               | InfluxDB 2.7              |
  +-----------+-----------+                                               | - Nanosecond Precision    |
              |                                                           | - High Insert Throughput  |
              |                                                           +-------------^-------------+
              | (MQTT Publish: Telemetry Topic)                                         | Line Protocol
              v                                                                         |
  +-----------------------+                                               +-------------+-------------+
  |   HAProxy Gateway     |                                               | Cloud Worker Daemon       |
  |   (Port 1883)         |                                               | - Thread Pooling          |
  |   TCP Round-Robin     |                                               | - Zlib Decompressor       |
  +-------+-------+-------+                                               | - NaN Engine Handlers     |
          |       |                                                       |                           |
          v       v                                                       | [ Rate Load Moderator ]   |
  +-------+-------+-------+   <========================================   | Evaluates ingress / CPU   |
  |   Mosquitto Cluster   |           (Subscribe: Telemetry Topic)        | limits and calculates safe|
  |  [node1]     [node2]  |                                               | publish velocities.       |
  |      [node-n]         |   ========================================>   +---------------------------+
  +-----------------------+       (Publish: Modulation Control Topic)       
              ^                                                           
              | (Feedback Command Loop)                                    
              |                                                           
              +---------------------------------------------------------------------------------------+
                                                                                                      |
  [ JSON "Slow Down! / Speed Up!" commands seamlessly propagate back to the Subscribed Edge network ]-+

===============================================================================================================
```

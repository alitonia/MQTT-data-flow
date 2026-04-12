# Dynamic Rate Modulation Implementation Plan

**Objective:** Implement a bidirectional feedback loop enabling the centralized Cloud environment to throttle, modulate, or accelerate the publish rates of the distributed Edge devices based on server load, creating a fully dynamic telemetry ingestion pipeline.

---

## 1. Architectural Approach
Currently, communication is one-way: `Edge -> Gateway -> Broker -> Cloud`. 
To implement dynamic rate modulation, we will build a **Feedback Control Loop** using a dedicated MQTT Control Topic. 

- **Data Topic**: `factory/turbofan/data` (Existing)
- **Control Topic**: `factory/control/modulation` (New)

The Cloud Worker will monitor system telemetry and publish global or targeted rate-limits to the Control Topic. All Edge Nodes will act as subscribers to this Control Topic, instantaneously updating their internal processing delays in response to the Cloud's commands.

## 2. Component Implementation Details

### A. Edge Node Updates (`edge/main.py` & `edge-wild/main.py`)
The edge systems need to shift from static environment variables to dynamic state configurations.
1. **Subscriptions**: In the `on_connect` callback, subscribe to `factory/control/modulation`.
2. **State Variables**: Convert the static `SIM_DELAY` and `BATCH_SIZE` variables into global, mutable states.
3. **Control Handler**: Create a new `on_control_message(client, userdata, msg)` callback to parse JSON directives sent from the server.
   *Example command expected:* 
   ```json
   {
     "target_node": "all",  // Can be "all" or a specific "unit_id"
     "new_delay_sec": 0.5,
     "new_batch_size": 20
   }
   ```
4. **Thread Safety**: Wrap the `SIM_DELAY` updates using a `threading.Lock()` to prevent race conditions during the core `process_data()` loop evaluation.

### B. Cloud Worker Updates (`cloud/main.py`)
The Cloud Worker needs intelligence to decide *when* to send these modulation packets back to the edge.

1. **Load Monitoring Agent**: Add a background thread specifically for tracking execution queue and CPU boundaries. 
   - If the average processing time of a batch exceeds the ingestion window (e.g., if there is severe DB backpressure), the pipeline is bottlenecking.
2. **Threshold Decisions (Simple P-Controller)**:
   - **Condition Overload**: If InfluxDB rejects requests or processing time drops severely, explicitly publish a slow-down command to the control topic: `{"target_node": "all", "new_delay_sec": 1.0}`.
   - **Condition Safe**: If the CPU load stays below 30% for 30 seconds, incrementally publish a speed-up command: `{"new_delay_sec": 0.2}`.
3. **MQTT Publish Logic**: Allow the Cloud Worker's multi-threaded client not just to consume, but actively `.publish()` via the primary HAProxy cluster route it is already attached to.

## 3. Step-by-Step Execution Checklist
*(Do not configure yet. This is your roadmap for execution).*

- **Phase 1: Edge Subscription Logic**
  - [ ] Add `client.message_callback_add()` specifically for the new control topic on all python edge nodes.
  - [ ] Refactor the `while True` delays to pull tightly from the dynamic global variable rather than the initial `os.getenv`.

- **Phase 2: Cloud Publisher Loop**
  - [ ] Build a `CloudModerator` thread that calculates message arrival velocity inside `cloud/main.py`.
  - [ ] Write logic evaluating incoming message velocity vs processing speed.
  - [ ] Implement the `client.publish` payload broadcaster back to the `factory/control/modulation` channel.

- **Phase 3: Visualization & Dashboards**
  - [ ] Create a Grafana Panel labeled **"Dynamic Throttle Status"** tracking the integer value of the modulated delay currently commanded by the Server across the network.
  - [ ] Observe live demonstrations of traffic spikes being smoothly negotiated and lowered automatically by the server's load-balancing algorithm.

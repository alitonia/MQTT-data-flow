import os
import zlib
import json
import time
import datetime
import threading
import math

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


# ======================
# CONFIG
# ======================
MQTT_BROKERS = os.getenv("MQTT_BROKERS", "mosquitto1,mosquitto2").split(",")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "factory/turbofan/data")

INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "my-super-secret-auth-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "my-org")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "my-bucket")


# ======================
# INFLUX CLIENT (shared)
# ======================
influx_client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

write_api = influx_client.write_api(write_options=SYNCHRONOUS)

# ======================
# RATE MODULATION STATE
# ======================
message_count = 0
load_lock = threading.Lock()
current_edge_delay = 0.1
primary_mqtt_client = None


# ======================
# CALLBACKS
# ======================
def on_connect(client, userdata, flags, rc):
    global primary_mqtt_client
    broker = userdata["broker"]
    if rc == 0:
        print(f"✅ Connected to {broker}")
        client.subscribe(MQTT_TOPIC)
        # Capture one successful client capability to publish feedback commands
        if primary_mqtt_client is None:
            primary_mqtt_client = client
    else:
        print(f"❌ Failed to connect to {broker}, rc={rc}")


def on_message(client, userdata, msg):
    broker = userdata["broker"]

    try:
        decompressed = zlib.decompress(msg.payload)
        batch = json.loads(decompressed.decode("utf-8"))

        points = []

        print(f"\n[{broker}] Received batch with {len(batch)} records")

        for idx, data in enumerate(batch, start=1):
            dataset = data.get("dataset", "unknown")
            unit = data.get("unit")
            cycle = data.get("cycle")
            timestamp_ns = data.get("timestamp_ns")
            sensors = data.get("sensors", [])

            # convert timestamp để log
            dt = datetime.datetime.fromtimestamp(timestamp_ns / 1e9)
            time_str = dt.strftime("%H:%M:%S.%f")[:-3]

            print(
                f"[{broker}] [{dataset}]  {time_str} | "
                f"Record {idx}/{len(batch)} | "
                f"Unit {unit} | Cycle {cycle}"
            )

            p = (
                Point("turbofan_telemetry")
                .tag("dataset", dataset)
                .tag("unit", str(unit))
                .field("cycle", cycle)
            )

            # ======================
            # GIỮ NGUYÊN LOGIC NaN
            # ======================
            for i, s_val in enumerate(sensors):
                if s_val is not None:
                    p = p.field(f"sensor_{i + 1}", float(s_val))
                else:
                    print(
                        f" [{broker}] Missing sensor_{i + 1} | "
                        f"Unit {unit} | Cycle {cycle}"
                    )
                    p = p.field(f"sensor_{i + 1}", float("nan"))

            # giữ timestamp từ edge
            p = p.time(timestamp_ns)
            points.append(p)

        # write xuống InfluxDB
        write_api.write(
            bucket=INFLUX_BUCKET,
            org=INFLUX_ORG,
            record=points
        )

        global message_count
        with load_lock:
            message_count += len(points)

        print(f" [{broker}] Wrote {len(points)} records to InfluxDB\n")

    except Exception as e:
        print(f" [{broker}] Error processing message: {e}")

# ======================
# MODERATOR THREAD
# ======================
def cloud_moderator_loop():
    global message_count, current_edge_delay, primary_mqtt_client
    while True:
        time.sleep(10) # Evaluate loads every 10 seconds
        
        with load_lock:
            rate = message_count / 10.0
            message_count = 0
            
        if not primary_mqtt_client:
            continue
            
        new_delay = current_edge_delay
        
        # 300 msg/s indicates bottleneck territory where we command Edge sensors to slow back
        if rate > 300: 
            new_delay = min(1.0, current_edge_delay + 0.1)
        # < 100 msg/s means we have deep buffer capability; tell devices they can speed up natively
        elif rate < 100: 
            new_delay = max(0.01, current_edge_delay - 0.05)
            
        new_delay = round(new_delay, 3)
        if new_delay != current_edge_delay:
            current_edge_delay = new_delay
            print(f"\n🚦 [CLOUD CONTROLLER] Inbound Ingestion Rate is {rate} msg/sec.")
            print(f"🚦 [CLOUD CONTROLLER] Broadcasting new commanded Edge publish delay: {current_edge_delay}s\n")
            payload = json.dumps({"new_delay_sec": current_edge_delay})
            primary_mqtt_client.publish("factory/control/modulation", payload, qos=1)


# ======================
# MQTT CLIENT THREAD
# ======================
def start_client(broker):
    while True:
        try:
            client = mqtt.Client(userdata={"broker": broker})
            client.on_connect = on_connect
            client.on_message = on_message

            print(f" Connecting to {broker}:{MQTT_PORT} ...")
            client.connect(broker, MQTT_PORT, 60)

            client.loop_forever()

        except Exception as e:
            print(f" {broker} connection failed: {e}. Retrying in 5s...")
            time.sleep(5)


# ======================
# MAIN
# ======================
def main():
    print(" Starting multi-broker cloud worker...")

    threads = []

    for broker in MQTT_BROKERS:
        broker = broker.strip()
        t = threading.Thread(target=start_client, args=(broker,))
        t.daemon = True
        t.start()
        threads.append(t)

    # Launch dynamic rate moderator
    t_mod = threading.Thread(target=cloud_moderator_loop, daemon=True)
    t_mod.start()

    # giữ process sống
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
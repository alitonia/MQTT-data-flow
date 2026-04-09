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
# CALLBACKS
# ======================
def on_connect(client, userdata, flags, rc):
    broker = userdata["broker"]
    if rc == 0:
        print(f"✅ Connected to {broker}")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ Failed to connect to {broker}, rc={rc}")


def on_message(client, userdata, msg):
    broker = userdata["broker"]

    try:
        decompressed = zlib.decompress(msg.payload)
        batch = json.loads(decompressed.decode("utf-8"))

        points = []

        print(f"\n📥 [{broker}] Received batch with {len(batch)} records")

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
                f"[{broker}] [{dataset}] ⏱ {time_str} | "
                f"📡 Record {idx}/{len(batch)} | "
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
                        f"⚠️ [{broker}] Missing sensor_{i + 1} | "
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

        print(f"✅ [{broker}] Wrote {len(points)} records to InfluxDB\n")

    except Exception as e:
        print(f"❌ [{broker}] Error processing message: {e}")


# ======================
# MQTT CLIENT THREAD
# ======================
def start_client(broker):
    while True:
        try:
            client = mqtt.Client(userdata={"broker": broker})
            client.on_connect = on_connect
            client.on_message = on_message

            print(f"🔌 Connecting to {broker}:{MQTT_PORT} ...")
            client.connect(broker, MQTT_PORT, 60)

            client.loop_forever()

        except Exception as e:
            print(f"⚠️ {broker} connection failed: {e}. Retrying in 5s...")
            time.sleep(5)


# ======================
# MAIN
# ======================
def main():
    print("🚀 Starting multi-broker cloud worker...")

    threads = []

    for broker in MQTT_BROKERS:
        broker = broker.strip()
        t = threading.Thread(target=start_client, args=(broker,))
        t.daemon = True
        t.start()
        threads.append(t)

    # giữ process sống
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
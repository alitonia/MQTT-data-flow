import os
import zlib
import json
import time
import datetime
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import math

#MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_BROKER = os.getenv('MQTT_BROKER', 'haproxy')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'factory/turbofan/data')

INFLUX_URL = os.getenv('INFLUX_URL', 'http://localhost:8086')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN', 'my-super-secret-auth-token')
INFLUX_ORG = os.getenv('INFLUX_ORG', 'my-org')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET', 'my-bucket')

influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    import datetime

    try:
        decompressed = zlib.decompress(msg.payload)
        batch = json.loads(decompressed.decode('utf-8'))

        points = []
        print(f"\nReceived batch with {len(batch)} records")

        for idx, data in enumerate(batch, start=1):
            dataset = data.get('dataset', 'unknown')
            unit = data.get('unit')
            cycle = data.get('cycle')
            timestamp_ns = data.get('timestamp_ns')
            sensors = data.get('sensors', [])

            # Convert timestamp giống edge
            dt = datetime.datetime.fromtimestamp(timestamp_ns / 1e9)
            time_str = dt.strftime('%H:%M:%S.%f')[:-3]

            # Log chi tiết từng record
            print(
                f"[{dataset}] {time_str} | "
                f"Received record {idx}/{len(batch)} | "
                f"Unit {unit} | Cycle {cycle}"
            )

            p = Point("turbofan_telemetry") \
                .tag("dataset", dataset) \
                .tag("unit", str(unit)) \
                .field("cycle", cycle)

            # for i, s_val in enumerate(sensors):
            #     p = p.field(f"sensor_{i + 1}", float(s_val))

            for i, s_val in enumerate(sensors):
                if s_val is not None:
                    p = p.field(f"sensor_{i + 1}", float(s_val))
                else:
                    print(f"[WARNING] Missing sensor_{i + 1} | Unit {unit} | Cycle {cycle}")
                    p = p.field(f"sensor_{i + 1}", float('nan'))

            # giữ timestamp từ edge
            p = p.time(timestamp_ns)
            points.append(p)

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)

        print(f"Wrote {len(points)} records to InfluxDB\n")

    except Exception as e:
        print(f"Error processing message: {e}")


def main():
    print(f"Starting cloud worker, connecting to InfluxDB at {INFLUX_URL}")
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except Exception as e:
            print(f"MQTT Broker not ready: {e}. Retrying in 5 seconds...")
            time.sleep(5)

    client.loop_forever()


if __name__ == "__main__":
    main()

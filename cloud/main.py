import os
import zlib
import json
import time
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
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
    try:
        decompressed = zlib.decompress(msg.payload)
        batch = json.loads(decompressed.decode('utf-8'))
        
        points = []
        for data in batch:
            dataset = data.get('dataset', 'unknown')
            unit = data.get('unit')
            cycle = data.get('cycle')
            timestamp_ns = data.get('timestamp_ns')
            sensors = data.get('sensors', [])
            
            p = Point("turbofan_telemetry") \
                .tag("dataset", dataset) \
                .tag("unit", str(unit)) \
                .field("cycle", cycle)
            
            for i, s_val in enumerate(sensors):
                p = p.field(f"sensor_{i+1}", float(s_val))
            
            # Use the actual timestamp from the edge
            p = p.time(timestamp_ns)
            points.append(p)
            
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
        print(f"Processed and wrote payload containing {len(points)} records to InfluxDB")
            
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

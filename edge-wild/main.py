import os
import json
import time
import zlib
import sqlite3
import threading
import random
import paho.mqtt.client as mqtt

MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'factory/turbofan/data')
NODE_ID = os.getenv('NODE_ID', 'wild-01')
DB_FILE = os.getenv('DB_FILE', f'buffer_{NODE_ID}.db')
DATASET = f"wild_{NODE_ID}"
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 10))

# Global state
is_connected = False
db_lock = threading.Lock()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  payload BLOB,
                  published INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def store_message(payload_bytes):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO messages (payload, published) VALUES (?, 0)", (payload_bytes,))
        conn.commit()
        conn.close()

def on_connect(client, userdata, flags, rc):
    global is_connected
    if rc == 0:
        print(f"[{NODE_ID}] Connected to MQTT Broker!")
        is_connected = True
    else:
        print(f"[{NODE_ID}] Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    global is_connected
    print(f"[{NODE_ID}] Disconnected from MQTT Broker!")
    is_connected = False

def publish_worker(client):
    global is_connected
    while True:
        if is_connected:
            try:
                with db_lock:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("SELECT id, payload FROM messages WHERE published = 0 LIMIT 10")
                    rows = c.fetchall()
                    for row in rows:
                        msg_id, payload = row
                        result = client.publish(MQTT_TOPIC, payload, qos=1)
                        if result.rc == mqtt.MQTT_ERR_SUCCESS:
                            c.execute("UPDATE messages SET published = 1 WHERE id = ?", (msg_id,))
                    
                    c.execute("DELETE FROM messages WHERE published = 1")
                    conn.commit()
                    conn.close()
            except Exception as e:
                print(f"[{NODE_ID}] Error in publish worker: {e}")
        time.sleep(2)

def generate_data(client):
    cycle = 1
    unit = 1
    batch = []
    
    # Base levels for 21 sensors (inspired by NASA dataset)
    base_sensors = [random.uniform(10, 500) for _ in range(21)]
    
    while True:
        # Simulate slight random walk + degradation
        # Degradation trend: sensors slowly drift
        sensors = []
        for i, base in enumerate(base_sensors):
            drift = (cycle * 0.01) * random.uniform(-1, 2) # Slight upward trend on average
            noise = random.uniform(-1, 1)
            sensors.append(base + drift + noise)
            
        data_point = {
            "dataset": DATASET,
            "unit": unit,
            "cycle": cycle,
            "timestamp_ns": time.time_ns(),
            "sensors": sensors
        }
        batch.append(data_point)
        
        if len(batch) >= BATCH_SIZE:
            payload_str = json.dumps(batch)
            compressed_payload = zlib.compress(payload_str.encode('utf-8'))
            store_message(compressed_payload)
            print(f"[{NODE_ID}] Buffered wildcard batch, cycle {cycle}")
            batch = []
            
        cycle += 1
        # Reset cycle occasionally to simulate new unit
        if cycle > 500:
            cycle = 1
            unit += 1
            base_sensors = [random.uniform(10, 500) for _ in range(21)]
            
        time.sleep(float(os.getenv('SIM_DELAY', 0.1)))

def main():
    init_db()
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    t = threading.Thread(target=publish_worker, args=(client,), daemon=True)
    t.start()
    
    print(f"[{NODE_ID}] Connecting to broker {MQTT_BROKER}...")
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except Exception as e:
            print(f"[{NODE_ID}] Broker not ready ({e}). Retrying in 5s...")
            time.sleep(5)
            
    client.loop_start()
    generate_data(client)

if __name__ == "__main__":
    main()

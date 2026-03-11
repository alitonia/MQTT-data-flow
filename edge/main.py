import os
import json
import time
import zlib
import sqlite3
import threading
import paho.mqtt.client as mqtt

MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'factory/turbofan/data')
DATA_FILE = os.getenv('DATA_FILE', 'data/train_FD001.txt')
DB_FILE = os.getenv('DB_FILE', 'buffer.db')
DATASET = os.path.splitext(os.path.basename(DATA_FILE))[0] # e.g., train_FD001
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
    return conn

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
        print("Connected to MQTT Broker!")
        is_connected = True
    else:
        print(f"Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    global is_connected
    print("Disconnected from MQTT Broker!")
    is_connected = False

def publish_worker(client):
    global is_connected
    while True:
        if is_connected:
            with db_lock:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT id, payload FROM messages WHERE published = 0 LIMIT 10")
                rows = c.fetchall()
                for row in rows:
                    msg_id, payload = row
                    result = client.publish(MQTT_TOPIC, payload, qos=1) # QoS 1 for at least once
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        c.execute("UPDATE messages SET published = 1 WHERE id = ?", (msg_id,))
                        print(f"Published buffered batch {msg_id}")
                
                # Delete published messages
                c.execute("DELETE FROM messages WHERE published = 1")
                conn.commit()
                conn.close()
        time.sleep(2)

def process_data(client):
    last_val = None
    batch = []
    
    try:
        with open(DATA_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 26:
                    continue
                unit = int(parts[0])
                cycle = int(parts[1])
                # Dummy metric: sum of sensors
                sensors = [float(x) for x in parts[5:]]
                current_metric = sum(sensors)
                
                # Pre-processing: Edge filtering
                # Only send if deviation > 0.1% compared to last sent value
                if last_val is None or abs(current_metric - last_val) / last_val > 0.001:
                    last_val = current_metric
                    data_point = {
                        "dataset": DATASET,
                        "unit": unit,
                        "cycle": cycle,
                        "timestamp_ns": time.time_ns(), # Use nano precision for InfluxDB
                        "sensors": sensors
                    }
                    batch.append(data_point)
                
                # Batching and compression
                if len(batch) >= BATCH_SIZE: # Batch size configurable
                    payload_str = json.dumps(batch)
                    compressed_payload = zlib.compress(payload_str.encode('utf-8'))
                    store_message(compressed_payload)
                    print(f"Buffered compressed batch of size {len(batch)}")
                    batch = []
                    
                time.sleep(float(os.getenv('SIM_DELAY', 0.1))) # Configurable delay
                
    except FileNotFoundError:
        print(f"Data file {DATA_FILE} not found.")
        
    # Flush remaining
    if batch:
        payload_str = json.dumps(batch)
        compressed_payload = zlib.compress(payload_str.encode('utf-8'))
        store_message(compressed_payload)
        print(f"Buffered compressed batch of size {len(batch)}")

def main():
    init_db()
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    # Run publish worker in background
    t = threading.Thread(target=publish_worker, args=(client,), daemon=True)
    t.start()
    
    print(f"Connecting to broker {MQTT_BROKER}:{MQTT_PORT}...")
    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            break
        except Exception as e:
            print(f"Broker not ready: {e}. Retrying in 5 seconds...")
            time.sleep(5)
            
    client.loop_start()
    
    print("Starting data processing...")
    process_data(client)
    
    # Wait for background queue to publish remaining messages
    time.sleep(10)
    print("Done processing, shutting down.")
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main()

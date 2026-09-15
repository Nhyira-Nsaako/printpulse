import csv
import json
import ssl
import signal
import sys
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

# ---- Broker settings (same as your ESP32 firmware) ----
MQTT_BROKER = "152fa86b7709460f8c860cd2732d9920.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "PrintPulse"
MQTT_PASSWORD = "FinalYearProject@2026"
MQTT_TOPIC = "printpulse/live"

OUTPUT_FILE = "vibration_log.csv"

csv_file = open(OUTPUT_FILE, "a", newline="")
csv_writer = csv.writer(csv_file)

# Write header only if the file is new/empty
if csv_file.tell() == 0:
    csv_writer.writerow(["received_at", "vibe_x", "vibe_y", "vibe_z", "vibe_mag"])
    csv_file.flush()

row_count = 0


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connected to broker. Subscribing to {MQTT_TOPIC}...")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Connection failed with code {rc}")


def on_message(client, userdata, msg):
    global row_count
    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print(f"Skipping non-JSON message: {msg.payload}")
        return

    x = payload.get("vibe_x")
    y = payload.get("vibe_y")
    z = payload.get("vibe_z")
    mag = payload.get("vibe_mag")

    # Older firmware doesn't send vibe_mag directly — compute it if missing.
    if mag is None and None not in (x, y, z):
        mag = (x**2 + y**2 + z**2) ** 0.5

    received_at = datetime.now(timezone.utc).isoformat()
    csv_writer.writerow([received_at, x, y, z, mag])

    row_count += 1
    if row_count % 50 == 0:
        csv_file.flush()  # periodic flush so you don't lose data on a crash
        print(f"{row_count} readings logged...")


def shutdown(signum=None, frame=None):
    print(f"\nStopping. {row_count} readings saved to {OUTPUT_FILE}.")
    csv_file.flush()
    csv_file.close()
    client.disconnect()
    sys.exit(0)


client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
client.on_connect = on_connect
client.on_message = on_message

signal.signal(signal.SIGINT, shutdown)   # Ctrl+C
signal.signal(signal.SIGTERM, shutdown)

print(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
client.loop_forever()

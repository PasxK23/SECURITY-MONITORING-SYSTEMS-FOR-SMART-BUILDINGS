import os
import time
import random
import json
import paho.mqtt.client as mqtt

BROKER_HOST = "emqx"
BROKER_PORT = int(os.getenv("BROKER_PORT", 1883))
DEVICE_ID = os.getenv("DEVICE_ID", f"Sensor_{random.randint(100, 999)}")
TOPIC = os.getenv("TOPIC", "building/general")  # temp, door, energy, smoke


def on_connect(client, userdata, flags, rc):
    print(f"[{DEVICE_ID}] Connected with result code {rc}")


client = mqtt.Client(client_id=DEVICE_ID)
client.on_connect = on_connect
try:
    client.connect(BROKER_HOST, BROKER_PORT, 60)
except:
    print(f"[{DEVICE_ID}] Connection to broker failed.")
    exit(1)
client.loop_start()

try:
    while True:
        payload = {}
        qos = 0
        retain = False
        sleep_time = 10

        if DEVICE_ID.startswith("DoorSensor"):
            sleep_time = random.uniform(5, 20)
            state = random.choices(["CLOSED", "OPEN"], weights=[0.95, 0.05])[0]
            payload = {"device": DEVICE_ID, "state": state}
            qos = 1
            if sleep_time > 10:
                retain = True

        elif DEVICE_ID.startswith("Meter"):
            sleep_time = random.uniform(2, 10)
            power = round(random.uniform(1.5, 5.0), 3)
            payload = {"device": DEVICE_ID, "power_kw": power}
            qos = 0

        elif DEVICE_ID.startswith("SmokeDetector"):
            sleep_time = 60
            state = random.choices(["OK", "ALARM"], weights=[0.95, 0.05], k=1)[0]
            battery = round(random.uniform(20.0, 100.0), 2)
            payload = {"device": DEVICE_ID, "status": state, "battery": battery}
            qos = 2
            retain = True

        elif DEVICE_ID.startswith("TempSensor"):
            sleep_time = random.uniform(5, 10)
            temp = round(random.uniform(20.0, 25.0), 2)
            humidity = round(random.uniform(40.0, 55.0), 2)
            payload = {"device": DEVICE_ID, "temp": temp, "humidity": humidity}
            qos = 1

        time.sleep(sleep_time)
        client.publish(TOPIC, json.dumps(payload), qos=qos, retain=retain)
        print(f"[{DEVICE_ID}] Published payload: {payload} at {time.ctime()}")

except KeyboardInterrupt:
    client.disconnect()

import sys
import pyshark

import threading

import json

import redis
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict
import time
from numpy import log1p

from collections import Counter
import math
import os

DOS_LIMIT = 8  # Max 8 πακέτα/δευτερόλεπτο (για PUBLISH)
BRUTE_FORCE_LIMIT = 6

security_lock = threading.Lock()  # Για τους μετρητές


REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")


def connect_to_redis():
    print(f"Attempting to connect to Redis at {REDIS_HOST}...", flush=True)
    attempts = 0
    while attempts < 10:
        try:
            r = redis.from_url(f"redis://{REDIS_HOST}:{6379}", decode_responses=True)

            if r.ping():
                print("Successfully connected to Redis!", flush=True)
                return r
        except Exception as e:
            attempts += 1
            print(
                f"Redis connection failed (Attempt {attempts}/10). Error: {e}",
                flush=True,
            )
            time.sleep(3)
    print(
        "[CRITICAL] Could not connect to Redis after 10 attempts. Exiting...",
        flush=True,
    )
    sys.exit(1)


r = connect_to_redis()
executor = ThreadPoolExecutor(max_workers=4)

# Μετρητές για DoS (μηδενίζουν κάθε δευτερόλεπτο)
packet_counts = defaultdict(int)
last_dos_reset = time.time()

# Μετρητές για Brute Force (μηδενίζουν κάθε 60 δευτερόλεπτα)
connect_counts = defaultdict(int)
last_bf_reset = time.time()


def check_dos(client_id):
    """Ελέγχει αν ο client στέλνει υπερβολικά πολλά πακέτα (Rate Limiting)"""
    global last_dos_reset
    with security_lock:
        current_time = time.time()

        if current_time - last_dos_reset > 1.0:
            packet_counts.clear()
            last_dos_reset = current_time

        packet_counts[client_id] += 1
        if packet_counts[client_id] > DOS_LIMIT:
            r.sadd(
                "dos_alerts",
                json.dumps({"clientid": client_id}),
            )

            return True
    return False


def check_brute_force(client_id):
    """Ελέγχει αν ο client κάνει πολλές επανασυνδέσεις (Connect Flooding)"""
    global last_bf_reset
    with security_lock:
        current_time = time.time()
        # 1. Reset κάθε 60 δευτερόλεπτα
        if current_time - last_bf_reset > 60.0:
            connect_counts.clear()
            last_bf_reset = current_time

        connect_counts[client_id] += 1
        if connect_counts[client_id] > BRUTE_FORCE_LIMIT:
            return True
    return False


def calculate_entropy(payload_hex):
    if len(payload_hex) > 512:
        payload_hex = payload_hex[:512]
    # Μετατροπή hex σε bytes
    data = bytes.fromhex(payload_hex.replace(":", ""))
    if not data:
        return 0

    entropy = 0
    length = len(data)

    counts = Counter(data)

    for count in counts.values():
        p_x = count / length
        entropy += -p_x * math.log2(p_x)
    return entropy


def process_packet(packet):
    try:
        features = {f: 0 for f in MQTT_FIELDS}
        try:
            tcp_stream = packet.tcp.stream
            msg_type = getattr(packet.mqtt, "msgtype", None)
        except AttributeError:
            tcp_stream = None
        features["ip"] = packet.ip.src

        if msg_type == "1" and tcp_stream is not None:
            client_id = str(getattr(packet.mqtt, "clientid", 0))
            print(
                f"[DEBUG] MQTT CONNECT detected. Client ID: {client_id}, Stream: {tcp_stream}"
            )
            if client_id and tcp_stream:
                if check_brute_force(client_id):
                    print(
                        f"[ALERT] Brute Force detected: {client_id}. Dropping packet."
                    )
                    r.rpush(
                        "score_updates",
                        json.dumps(
                            {
                                "clientid": client_id,
                                "clientip": features["ip"],
                                "proba": 2.0,
                            }
                        ),
                    )
                    return

                r.hset("stream_to_client", tcp_stream, client_id)
                r.expire("stream_to_client", 3600)

                # RESET ΤΑ CLOCKS ΓΙΑ ΝΕΟ SESSION
                r.delete(f"vclock:{client_id}")
                r.delete(f"auth_seq:{client_id}")
                r.delete(f"queue:{client_id}")
                return

        elif msg_type == "3":
            clientid = r.hget("stream_to_client", tcp_stream)
            if clientid:
                if "MQTT" in packet:

                    payload_hex = getattr(packet.mqtt, "msg", 0)
                    features["mqtt.payload_entropy"] = calculate_entropy(payload_hex)
                    features["mqtt_len_log"] = float(
                        log1p(float(getattr(packet.mqtt, "len", 0)))
                    )
                    features["mqtt.topic.len"] = len(getattr(packet.mqtt, "topic", 0))
                    features["mqtt.qos"] = getattr(packet.mqtt, "qos", 0)
                    features["mqtt.retain"] = getattr(packet.mqtt, "retain", 0)
                    features["mqtt.retain"] = (
                        1 if features["mqtt.retain"] == "True" else 0
                    )
                    features["timestamp"] = time.time()

                if "TCP" in packet:
                    features["tcp.time_delta"] = getattr(packet.tcp, "time_delta", 0)
                    features["tcp.len"] = getattr(packet.tcp, "len", 0)

                if check_dos(clientid):
                    print(f"[ALERT] DoS Attack detected: {clientid}. Dropping packet.")
                    r.rpush(
                        "score_updates",
                        json.dumps(
                            {
                                "clientid": clientid,
                                "clientip": features["ip"],
                                "proba": 1.0,
                            }
                        ),
                    )
                    return
                send_to_redis(features, clientid)

        elif msg_type == "14":
            if tcp_stream is not None:
                r.hdel("stream_to_client", tcp_stream)
                print(f"[INFO] MQTT Disconnect for stream: {tcp_stream}")

    except Exception as e:
        print(f"[ERROR] Processing packet: {e}")
        pass


def send_to_redis(features, clientid=None):

    current_vclock = r.incr(f"vclock:{clientid}")
    features["vclock"] = current_vclock
    print(f"ROUTING TO API_2 on {time.ctime()}:{clientid}:{features}", flush=True)
    if clientid:
        r.rpush(f"queue:{clientid}", json.dumps(features))
    else:
        print("[WARN] No clientid found for features, not storing in Redis.")


INTERFACE = r"bridge"


capture = pyshark.LiveCapture(
    interface=INTERFACE,
    bpf_filter="tcp dst port 1883",
    display_filter="mqtt.msgtype == 1 || mqtt.msgtype == 3 || mqtt.msgtype == 14",
)

print(f"[INFO] Sniffing on this interface: {INTERFACE}", flush=True)

MQTT_FIELDS = [
    "tcp.time_delta",
    "tcp.len",
    "mqtt.retain",
    "mqtt.qos",
    "mqtt_len_log",
    "mqtt.payload_entropy",
    "mqtt.topic.len",
]


for packet in capture.sniff_continuously():
    executor.submit(process_packet, packet)

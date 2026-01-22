import threading
import redis
import subprocess
import os
import requests
import base64
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

EMQX_HOST = os.getenv("EMQX_API_HOST", "emqx")
API_KEY = os.getenv("EMQX_API_KEY", "your_api_key_here")
API_SECRET_KEY = os.getenv("EMQX_API_SECRET_KEY", "your_api_secret_here")
EMQX_API = f"http://{EMQX_HOST}:18083/api/v5/banned"

REDIS_HOST = os.getenv("REDIS_HOST", "redis-service.emqx")
r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

executor = ThreadPoolExecutor(max_workers=8)
ban_lock = threading.Lock()


def apply_ban(ip):
    try:
        with ban_lock:
            check_cmd = f"iptables -t raw -C PREROUTING -s {ip} -j DROP"
            result = subprocess.run(check_cmd, shell=True, capture_output=True)

            if result.returncode != 0:
                ban_cmd = f"iptables -t raw -I PREROUTING -s {ip} -j DROP"
                subprocess.run(ban_cmd, shell=True, check=True)
                print(f"[BAN] Banned IP {ip} in RAW table (invisible to sniffer)")
            else:
                print(f"[BAN] IP {ip} is already banned in RAW table.")
    except Exception as e:
        print(f"[ERROR] Could not ban {ip}: {e}")


def emqx_client_ban(clientid):
    """Στέλνει εντολή στον EMQX να κανε ban  τη συσκευή"""

    api_key = API_KEY
    api_secret = API_SECRET_KEY
    auth_header = (
        "Basic " + base64.b64encode((api_key + ":" + api_secret).encode()).decode()
    )
    payload = {
        "as": "clientid",
        "who": clientid,
        "reason": "malicious_behavior",
        "until": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
    }

    req = requests.post(EMQX_API, json=payload, headers={"Authorization": auth_header})
    if req.status_code == 200:
        print(f"[BAN] Client {clientid} banned successfully")
    else:
        print(f"[ERROR] Could not ban client: {req.text}")


if __name__ == "__main__":
    print("Ban-Service is running (RAW TABLE mode)...")
    while True:
        result = r.blpop("ban_queue", timeout=0)
        if result:
            raw_data = result[1]
            target_ip, clientid = raw_data.split(",")
            executor.submit(apply_ban, target_ip)
            executor.submit(emqx_client_ban, clientid)

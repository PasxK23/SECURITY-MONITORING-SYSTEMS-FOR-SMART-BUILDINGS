import redis
import json
from concurrent.futures import ThreadPoolExecutor
import os


REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")
EMQX_HOST = os.getenv("EMQX_API_HOST", "emqx")
emqx_v = os.getenv("EMQX_VERSION")

print(f"--- System Info ---")
print(f"EMQX Version: {emqx_v}")


REDIS_PORT = 6379


# Παράμετροι Αλγορίθμου
W_PEN = 15.0
W_REW = 2.0
INITIAL_SCORE = 50.0
MAX_WORKERS = 20


r = redis.from_url(
    f"redis://{REDIS_HOST}:{REDIS_PORT}",
    decode_responses=True,
    health_check_interval=30,
)
LUA_UPDATE_SCORE = """
local score_key = KEYS[1]
local initial_score = tonumber(ARGV[1])
local delta = tonumber(ARGV[2])
local expire_time = tonumber(ARGV[3])
local client_ip = ARGV[4]
local client_id = ARGV[5]
local current_score = tonumber(redis.call('get', score_key))
if not current_score then
    current_score = initial_score
end

local new_score = current_score + delta
if new_score > 100 then new_score = 100 end
if new_score < 0 then new_score = 0 end
redis.call('set', score_key, new_score)
if new_score < 1 then
    redis.call('expire', score_key, expire_time)
    local ban_data = client_ip .. "," .. client_id
    redis.call('rpush', 'ban_queue', ban_data)
end

return new_score
"""
update_script = r.register_script(LUA_UPDATE_SCORE)


def calculate_change(proba):
    if proba > 0.5:
        return -(proba * W_PEN)
    else:
        return (1 - proba) * W_REW


def process_task(data_raw):
    """Η κύρια μονάδα εργασίας κάθε thread"""
    try:
        task = json.loads(data_raw)
        clientid = task["clientid"]
        clientip = task["clientip"]
        proba = task["proba"]

        delta = calculate_change(proba)

        score_key = f"score:{clientid}"
        new_score = update_script(
            keys=[score_key], args=[INITIAL_SCORE, delta, 86400, clientip, clientid]
        )

        print(
            f"[UPDATE] Client: {clientid} with IP: {clientip} | Δ: {delta:+.2f} | New Score: {new_score}"
        )

    except Exception as e:
        print(f"[THREAD ERROR] {e}")


def run_manager():
    print("Score Manager Worker Started. Listening for score_updates...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        while True:
            # Blocking pop από την ουρά
            result = r.blpop("score_updates", timeout=0)
            if result:
                print("Received score update task.")
                _, data_raw = result
                executor.submit(process_task, data_raw)


run_manager()

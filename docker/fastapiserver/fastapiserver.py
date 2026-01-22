from fastapi import FastAPI
import joblib
from pydantic import BaseModel
import uvicorn
import time
import json
import redis.asyncio as redis
from fastapi.concurrency import run_in_threadpool
from fastapi import BackgroundTasks
from numpy import array

REDIS_HOST = "redis-service"
REDIS_PORT = 6379
import joblib

model = joblib.load("rf_model.pkl")
import warnings

warnings.filterwarnings("ignore", category=UserWarning)
redis_con = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
app = FastAPI()

ordered_feature_names = list(model.feature_names_in_)


class AuthzRequest(BaseModel):
    clientid: str
    action: str


class ClientRequest(BaseModel):
    clientid: str


async def send_score_update(clientid: str, clientip: str, proba: float):
    update_task = {"clientid": clientid, "clientip": clientip, "proba": proba}
    await redis_con.rpush("score_updates", json.dumps(update_task))


async def predict_intrusion(
    clientid, features: dict, background_tasks: BackgroundTasks
) -> bool:

    ordered_features = [
        float(features.get(name, 0.0)) for name in ordered_feature_names
    ]
    features_array = array([ordered_features])
    try:
        prediction = await run_in_threadpool(model.predict_proba, features_array)
        proba = float(prediction[0][1])
    except Exception as e:
        print(f"[ERROR] Inference failed: {e}")
        return False

    background_tasks.add_task(send_score_update, clientid, features["ip"], proba)
    print(f"[ML MODEL] Prediction for Client {clientid}: {proba} on {time.ctime()}")

    return proba > 0.65


@app.post("/mqtt/authz")
async def check_authorization(req: AuthzRequest, background_tasks: BackgroundTasks):

    if req.action != "publish":
        print(
            f"[AUTHZ NON PUB] Non-publish action for Client: {req.clientid} and action: {req.action}. Allowing by default ."
        )
        return {"result": "allow"}
    print(
        f"[AUTHZ REQUEST] Authorization request for Client: {req.clientid} and time: {time.ctime()}",
        flush=True,
    )

    result = await redis_con.blpop(f"queue:{req.clientid}", timeout=5)
    if result:
        _, raw_data = result

        current_auth_clock = await redis_con.incr(f"auth_seq:{req.clientid}")
        features = json.loads(raw_data)
        actual_clock = int(features.get("vclock", 0))
        print(
            f"[DEBUG] Client {req.clientid}: Expected {current_auth_clock}, got {actual_clock}"
        )
        if actual_clock < current_auth_clock:
            print(
                f"[CAUSALITY WARN] Client {req.clientid}: Expected {current_auth_clock}, got {actual_clock}. Lag detected!"
            )

            while actual_clock < current_auth_clock:
                next_item = await redis_con.lpop(f"queue:{req.clientid}")
                if not next_item:
                    break
                features = json.loads(next_item)
                actual_clock = int(features.get("vclock", 0))
            print(f"[RECOVERY] Synced to clock {actual_clock}")

        elif actual_clock > current_auth_clock:
            print(
                f"[CRITICAL ERROR] Clock Inconsistency! Actual ({actual_clock}) > Expected ({current_auth_clock})"
            )

            await redis_con.set(f"vclock:{req.clientid}", actual_clock)

        is_attack = await predict_intrusion(req.clientid, features, background_tasks)

        if is_attack:
            return {"result": "deny"}
        else:
            return {"result": "allow"}
    else:
        if await redis_con.srem("dos_alerts", req.clientid):
            print(
                f"[AUTHZ DENY] No data found for Client: {req.clientid}. Denying due to DoS status."
            )
            return {"result": "deny"}
    print(f"[AUTHZ ALLOW] No data found for Client: {req.clientid}. Allowing.")

    return {"result": "allow"}


if __name__ == "__main__":
    uvicorn.run("fastapiserver:app", host="0.0.0.0", port=8080, workers=4)

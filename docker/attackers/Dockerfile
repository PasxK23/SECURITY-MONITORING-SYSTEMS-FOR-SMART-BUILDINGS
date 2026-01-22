FROM python:3.9-slim

WORKDIR /app

# Εγκατάσταση της βιβλιοθήκης paho-mqtt
RUN pip install --no-cache-dir paho-mqtt

# Αντιγραφή ρχείων πιτιθέμενων
COPY pub_control_mal.py .
COPY pub_flood.py .
COPY pub_fuzzer.py .
COPY pub_impostor.py .
COPY pub_qos_ex.py .
COPY pub_retain.py .
COPY pub_semant_fuzz.py .
COPY pub_stealth_flood.py .


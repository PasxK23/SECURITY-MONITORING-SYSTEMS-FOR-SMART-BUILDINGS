FROM python:3.11-slim


RUN apt-get update && \
    apt-get install -y tshark && \
    setcap 'CAP_NET_RAW+eip CAP_NET_ADMIN+eip' /usr/bin/dumpcap && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sniffer.py .

ENV PYTHONUNBUFFERED=1
CMD ["python", "sniffer.py"]

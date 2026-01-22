FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y iptables kmod && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ip_ban.py .


CMD ["python","ip_ban.py"]
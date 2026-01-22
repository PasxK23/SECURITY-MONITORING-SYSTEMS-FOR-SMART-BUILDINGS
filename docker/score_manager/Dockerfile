FROM python:3.9-slim

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1


COPY score_manager.py .


CMD ["python", "score_manager.py"]
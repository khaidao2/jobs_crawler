FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        netcat-openbsd \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY src/crawlers/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY src/crawlers /app/crawler
COPY schemas /app/schemas

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["sleep", "infinity"]
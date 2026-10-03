FROM python:3.12-slim-bookworm

WORKDIR /python-docker

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt \
    && playwright install --with-deps chromium

COPY . .

# Threads are required: GET / makes Chromium request /weather from this same process.
CMD [ "gunicorn", "--workers", "1", "--threads", "4", "--bind", "0.0.0.0:5000", "app:app" ]

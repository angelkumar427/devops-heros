# Build context: final-devops-project/application
# docker build -f docker/Dockerfile -t task-tracker application/
FROM python:3.12-slim

RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /data && chown appuser:appuser /data
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION} PORT=8080 DATA_DIR=/data PYTHONDONTWRITEBYTECODE=1
USER appuser
EXPOSE 8080

# One worker process with threads: every scrape of /metrics then sees the same registry.
# (With several workers each keeps its own counters, scrapes alternate between them and
#  rate() reads the jumps as counter resets.) Scale out with replicas, not workers.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--access-logfile", "-", "app.server:app"]

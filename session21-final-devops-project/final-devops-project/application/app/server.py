"""Task Tracker API - the application for the final DevOps project.

Exercises every platform feature the project needs:
  * config from a ConfigMap   (APP_ENV, LOG_LEVEL, MAX_TASKS)
  * a credential from a Secret (API_TOKEN, required for writes)
  * persistent storage         (tasks saved as JSON on a PersistentVolume)
  * health endpoints           (/healthz liveness, /readyz readiness)
  * Prometheus metrics         (/metrics)
"""
import fcntl
import json
import logging
import os
import socket
import threading
import time
from contextlib import contextmanager

from flask import Flask, abort, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest

APP_ENV = os.environ.get("APP_ENV", "dev")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
MAX_TASKS = int(os.environ.get("MAX_TASKS", "100"))
API_TOKEN = os.environ.get("API_TOKEN", "")
DATA_DIR = os.environ.get("DATA_DIR", "/data")
VERSION = os.environ.get("APP_VERSION", "dev")

logging.basicConfig(level=LOG_LEVEL, format='{"level":"%(levelname)s","ts":"%(asctime)s","msg":"%(message)s"}')
log = logging.getLogger("tasks")

app = Flask(__name__)
_lock = threading.Lock()

# A dedicated registry rather than the process-global default, so the module can be
# reloaded (as the tests do) without "Duplicated timeseries" errors.
REGISTRY = CollectorRegistry()
# The route label is "path", not "endpoint": Prometheus Operator attaches its own `endpoint`
# target label (the Service port name) and would silently rename ours to exported_endpoint.
REQUESTS = Counter("tasks_http_requests_total", "HTTP requests", ["method", "path", "status"], registry=REGISTRY)
# Buckets start at 0.5 ms: this API answers in ~1-3 ms, and with the default buckets (first
# one 5 ms) every request lands in one bucket, so p95 is just interpolated (a flat 4.75 ms).
LATENCY = Histogram("tasks_http_request_duration_seconds", "Request latency", ["path"], registry=REGISTRY,
                    buckets=(0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0))
TASKS = Gauge("tasks_stored", "Number of tasks currently stored", registry=REGISTRY)


def _path():
    return os.path.join(DATA_DIR, "tasks.json")


@contextmanager
def _locked():
    """Serialise read-modify-write of tasks.json.

    threading.Lock only covers the threads of one worker. gunicorn runs several worker
    processes and every replica mounts the same volume, so an flock on the volume is what
    actually stops two writers from losing each other's task. (RWO volumes are attached
    to a single node, where flock is honoured.)
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    with _lock, open(os.path.join(DATA_DIR, ".lock"), "a") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _load():
    try:
        with open(_path()) as fh:
            return json.load(fh)
    except FileNotFoundError:
        return []


def _save(tasks):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = _path() + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(tasks, fh)
    os.replace(tmp, _path())  # atomic rename: no half-written file on crash


@app.before_request
def _start():
    g.start = time.perf_counter()


@app.after_request
def _record(resp):
    path = request.url_rule.rule if request.url_rule else "unmatched"
    if path != "/metrics":
        REQUESTS.labels(request.method, path, resp.status_code).inc()
        LATENCY.labels(path).observe(time.perf_counter() - g.start)
    return resp


@app.get("/healthz")
def healthz():
    return jsonify(status="ok")


@app.get("/readyz")
def readyz():
    # Ready only if storage is writable AND the API token was provided.
    if not API_TOKEN:
        return jsonify(status="not ready", reason="API_TOKEN not configured"), 503
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        # Unique per pod and worker - replicas share the volume, and a shared probe file
        # lets one pod delete another's file mid-check and fail its readiness.
        probe = os.path.join(DATA_DIR, f".probe-{socket.gethostname()}-{os.getpid()}")
        with open(probe, "w") as fh:
            fh.write("ok")
        os.remove(probe)
    except OSError as exc:
        return jsonify(status="not ready", reason=f"storage not writable: {exc.strerror}"), 503
    return jsonify(status="ready", env=APP_ENV, version=VERSION)


@app.get("/metrics")
def metrics():
    # Read from disk at scrape time: a freshly started pod must report the stored tasks,
    # not 0 until its first write. (os.replace makes the file read atomic - no lock needed.)
    TASKS.set(len(_load()))
    return generate_latest(REGISTRY), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.get("/api/tasks")
def list_tasks():
    with _locked():
        return jsonify(_load())


@app.post("/api/tasks")
def create_task():
    if request.headers.get("Authorization") != f"Bearer {API_TOKEN}" or not API_TOKEN:
        abort(401, description="missing or invalid bearer token")
    title = (request.get_json(silent=True) or {}).get("title")
    if not isinstance(title, str) or not title.strip():
        abort(400, description="'title' must be a non-empty string")
    with _locked():
        tasks = _load()
        if len(tasks) >= MAX_TASKS:
            abort(409, description=f"task limit of {MAX_TASKS} reached")
        task = {"id": (max((t["id"] for t in tasks), default=0) + 1), "title": title.strip()[:200], "done": False}
        tasks.append(task)
        _save(tasks)
    log.info("task created id=%s", task["id"])
    return jsonify(task), 201


@app.get("/")
def index():
    return jsonify(service="task-tracker", env=APP_ENV, version=VERSION, endpoints=["/api/tasks", "/healthz", "/readyz", "/metrics"])


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(404)
@app.errorhandler(409)
def _err(err):
    return jsonify(error=err.description), err.code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))  # nosec B104 - container listens on all interfaces

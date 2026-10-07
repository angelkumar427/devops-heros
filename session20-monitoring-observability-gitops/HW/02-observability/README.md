# 02 — Observability

**Session 20 homework — Task 2** · Angel Kumar · 24bcs10011

## Monitoring vs observability

**Monitoring** answers questions you knew to ask in advance: *is the CPU above 80%? is the service up?* You define the checks; it tells you when one trips.

**Observability** is the ability to answer questions you **didn't** anticipate — *why are only some users in Mumbai seeing slow checkouts since 14:05?* — by exploring the data a system emits, without shipping new code to find out.

Monitoring tells you *that* something is wrong. Observability lets you work out *why*.

---

## The three pillars

### 1. Metrics — *what is happening, in numbers*

Numeric measurements over time, cheap to store and fast to query.

```
http_requests_total{status="200"}                   counter — only goes up
container_memory_working_set_bytes{pod="..."}       gauge   — goes up and down
http_request_duration_seconds_bucket{le="0.5"}      histogram — distribution of values
```

- **Best at:** trends, dashboards, alerting, capacity planning.
- **Weakness:** aggregated, so they tell you *that* error rate rose — not *which* request failed or why.
- **Watch out for cardinality:** every unique label combination is a new time series. A label like `user_id` can create millions and take Prometheus down.

**Seen in this session:** CPU, memory, request rate and `up` for the demo app, scraped every 15s by Prometheus — and both alerts were built on metrics. ([Monitoring](../01-monitoring/))

### 2. Logs — *what happened, in detail*

Timestamped records of discrete events.

```json
{"level":"info","ts":"2026-10-07T14:14:14.819Z","caller":"http/server.go:224","msg":"Starting HTTP Server.","addr":":9898"}
```

- **Best at:** the specific detail of an individual event — the error message, the stack trace, the payload that broke.
- **Weakness:** expensive at volume, and hard to correlate across services.
- **Structured (JSON) logs** like the one above are vastly more useful than free text: a log system can filter `level=error AND path=/checkout` instead of grepping.

**Seen in this session — and it's the case for having more than one pillar:** the load test sent tens of thousands of requests, but **none of them appear in the logs**, because podinfo only logs requests at debug level. The metrics recorded all of them (`HTTP 200` peaking near 28K req/s). Each pillar sees things the other doesn't.

### 3. Traces — *where the time went, across services*

A **trace** follows one request through every service it touches. Each hop is a **span** with a start time, duration and parent, linked by a shared **trace ID**.

```
Trace 7f3a9...  POST /checkout                         1,240 ms
├── api-gateway                                           12 ms
├── order-service      create order                       85 ms
│   └── postgres       INSERT orders                      61 ms
├── payment-service    charge card                     1,090 ms   <- the problem
│   └── stripe-api     POST /charges                   1,071 ms
└── notification-svc   send email                         40 ms
```

- **Best at:** finding *which* service in a chain of ten made a request slow, and the dependencies between them.
- **Weakness:** needs code instrumentation (or auto-instrumentation), and is usually **sampled** because storing every trace is costly.

### How they fit together

| Pillar | Answers | Cost | Typical tool |
|---|---|---|---|
| **Metrics** | *Is something wrong, and how much?* | Low | Prometheus |
| **Logs** | *What exactly happened?* | High at volume | Loki, Elasticsearch |
| **Traces** | *Where in the system did it happen?* | Medium, sampled | Jaeger, Tempo |

A real investigation uses all three in sequence: **an alert fires on a metric → the trace shows which service is slow → that service's logs show the exception.** The glue is correlation — a `trace_id` written into log lines, and *exemplars* linking a metric data point to a specific trace.

---

## Why observability is required

- **Distributed systems fail in novel ways.** With dozens of services, the failure you'll hit next is rarely one you wrote a check for in advance.
- **Kubernetes is ephemeral.** Pods are killed, rescheduled and replaced constantly; when a pod is gone, so are its local logs and state. Data has to be shipped somewhere durable *while* it exists.
- **Mean time to recovery.** Most of an incident's duration is spent *finding* the cause, not fixing it. Good observability shrinks that.
- **SLOs need data.** "99.9% of requests succeed in under 300 ms" is only a promise if it can be measured.
- **It catches the monitoring's own failures.** This session found an alert that matched no data and could never have fired ([details](../01-monitoring/#a-silent-alert--found-and-fixed)). Only by actually querying the data was that visible.

---

## Common tools

| Category | Tools |
|---|---|
| Metrics | **Prometheus**, Thanos / Mimir (long-term storage), Datadog, CloudWatch |
| Visualisation | **Grafana** |
| Alerting | **Alertmanager**, PagerDuty, Opsgenie |
| Logs | **Loki**, Elasticsearch / OpenSearch + Kibana (ELK), Fluent Bit / Fluentd (shippers) |
| Traces | **Jaeger**, Grafana Tempo, Zipkin |
| Instrumentation standard | **OpenTelemetry** — one vendor-neutral SDK and collector for metrics, logs *and* traces |
| All-in-one SaaS | Datadog, New Relic, Dynatrace, Honeycomb |

**OpenTelemetry** is the important trend: instrument once with an open standard, then send data to any backend, instead of locking code into one vendor's agent.

---

## Kubernetes observability

| Layer | What to watch | Source |
|---|---|---|
| **Cluster** | API server health, etcd, scheduling failures | Control-plane metrics |
| **Nodes** | CPU, memory, disk, network | **node-exporter** |
| **Kubernetes objects** | Desired vs available replicas, restarts, pod phases, PVC status | **kube-state-metrics** |
| **Containers** | CPU, memory, throttling, OOM kills | **cAdvisor** (inside the kubelet) |
| **Applications** | Request rate, errors, latency, business metrics | The app's own `/metrics` endpoint |
| **Events** | Scheduling failures, image pulls, probe failures | `kubectl get events` |

All of these except events were running in [the monitoring demo](../01-monitoring/), installed in one step by **kube-prometheus-stack**.

**Two useful signal frameworks:**

- **RED** for services — **R**ate, **E**rrors, **D**uration.
- **USE** for resources — **U**tilisation, **S**aturation, **E**rrors.

### A Kubernetes-specific lesson from this session

The standard container metrics carry a `container` label on most clusters. On this one (k3s with the Docker runtime) **they don't** — cAdvisor only reports pod-level cgroups. Every query, dashboard and alert filtering on `container="..."` silently returned nothing. Observability tooling makes assumptions about the platform underneath it, and those assumptions need checking against the real data rather than trusting that a dashboard "has no data" because things are quiet.

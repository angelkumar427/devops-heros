# Monitoring - Prometheus + Grafana

Installed with the community `kube-prometheus-stack` chart (Prometheus Operator, Prometheus,
Alertmanager, Grafana, node-exporter, kube-state-metrics):

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/kube-prometheus-stack-values.yaml
```

The StockPilot chart then plugs itself in - nothing to configure by hand:

| Object (in `helm/stockpilot/templates/`) | Effect |
|---|---|
| `ServiceMonitor` | Prometheus scrapes the backend's `/metrics` every 15 s |
| `PrometheusRule` | availability alerts (backend down, 5xx ratio, p95 latency, HPA at max) and a business alert (products below reorder level) |
| `ConfigMap` labelled `grafana_dashboard: "1"` | Grafana's sidecar loads the **StockPilot** dashboard automatically |

Open the UIs locally:

```bash
kubectl -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090
kubectl -n monitoring port-forward svc/monitoring-grafana 3000:80     # dashboard: /d/stockpilot
```

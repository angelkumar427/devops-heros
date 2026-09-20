# Task 4: CoreDNS in Kubernetes

**Author:** Angel Kumar · 24bcs10011  
**Repository:** [angelkumar427/devops-heros](https://github.com/angelkumar427/devops-heros)

This document provides an in-depth analysis of **CoreDNS**, the default DNS and service discovery server used in Kubernetes clusters.

---

## 1. What is CoreDNS?

**CoreDNS** is a fast, flexible, and modular DNS server written in Go. It is a CNCF graduated project and has served as the default internal cluster DNS provider in Kubernetes since Kubernetes `v1.13` (replacing the legacy `kube-dns`).

CoreDNS operates as an in-cluster Deployment within the `kube-system` namespace, exposed via a stable `ClusterIP` Service named `kube-dns` (historically retaining the name `kube-dns` for backwards compatibility).

---

## 2. Why Kubernetes Uses CoreDNS

Kubernetes adopted CoreDNS over the legacy `kube-dns` system for several key architectural reasons:

1. **Single Binary & Single Container:** Legacy `kube-dns` ran three separate containers (`kube-dns`, `dnsmasq`, and `sidecar`). CoreDNS runs as a single, lightweight Go process, drastically reducing memory footprint and container lifecycle complexity.
2. **Extensible Plugin Architecture:** CoreDNS is built entirely out of chained plugins (`kubernetes`, `errors`, `health`, `cache`, `forward`, `prometheus`). Every feature is a pluggable middleware module.
3. **Direct Kubernetes API Watching:** The `kubernetes` plugin connects directly to the Kubernetes API server and dynamically watches `Service` and `EndpointSlice` resources, maintaining in-memory DNS tables in near real-time.
4. **Native Metrics:** Built-in Prometheus metrics export on port 9153 provides out-of-the-box visibility into query latency, cache hit ratios, and error rates.

---

## 3. How Service Discovery Works

1. When a developer creates a Service (e.g., `web-service` in namespace `default` with type `ClusterIP`):
   - The Kubernetes API server writes the Service specification to etcd.
   - CoreDNS watches the API server via its `kubernetes` plugin.
   - CoreDNS dynamically creates an `A` record pointing `web-service.default.svc.cluster.local` to the allocated ClusterIP.
2. When Pods back that Service:
   - The EndpointSlice controller tracks the Pod IP addresses.
   - If the Service is Headless (`clusterIP: None`), CoreDNS creates an `A` record for each healthy endpoint Pod IP.
   - When a Pod dies or scales out, CoreDNS updates its internal lookup tables instantly based on API server events.

---

## 4. How DNS Queries Are Resolved

When an application container issues a network request to an address (e.g., `curl http://api-server`):

```
Application Pod (/etc/resolv.conf)
       │
       ▼
 CoreDNS Server (10.43.0.10:53)
       │
       ├────► Is it a cluster Service (*.svc.cluster.local)?
       │         └── YES ──► Return Service ClusterIP from memory
       │
       ├────► Is it a Pod FQDN (*.pod.cluster.local)?
       │         └── YES ──► Return Pod IP
       │
       └────► Is it an external internet domain (e.g., github.com)?
                 └── YES ──► Forward query to upstream resolver (/etc/resolv.conf of host)
```

1. **Local Resolver:** The pod's C library reads `/etc/resolv.conf` (pointing to CoreDNS ClusterIP `10.43.0.10`).
2. **Search Domains:** If a short name like `api-server` is queried, the search domains (`default.svc.cluster.local`, `svc.cluster.local`, `cluster.local`) are appended sequentially until a match is found.
3. **Plugin Chain Execution:**
   - `errors` logs failures.
   - `health` validates server liveness.
   - `kubernetes` checks if the requested domain matches the internal cluster zone. If matched, it returns the ClusterIP.
   - `forward` forwards non-cluster queries (like `google.com`) to the upstream DNS servers configured on the host node.
   - `cache` caches the response according to TTL.

---

## 5. CoreDNS Configuration (The Corefile)

CoreDNS configuration is managed declaratively via a `ConfigMap` named `coredns` in the `kube-system` namespace. Below is a production Corefile example:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health {
           lameduck 5s
        }
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
           pods insecure
           fallthrough in-addr.arpa ip6.arpa
           ttl 30
        }
        prometheus :9153
        forward . /etc/resolv.conf {
           max_concurrent 1000
        }
        cache 30
        loop
        reload
        loadbalance
    }
```

### Explanation of Core Plugins:
- `errors`: Logs DNS query errors to stdout.
- `health`: Exposes an HTTP health-check endpoint on port 8080.
- `ready`: Reports readiness on port 8181 to ensure traffic isn't routed before initialization.
- `kubernetes`: Implements the Kubernetes DNS specification for cluster domain `cluster.local`.
- `prometheus`: Exports query and performance metrics for Prometheus scraping.
- `forward`: Forwards external internet DNS requests to the host system's nameserver.
- `cache`: In-memory TTL cache (default 30 seconds) reducing load on CoreDNS and API server.
- `reload`: Automatically reloads the Corefile whenever the ConfigMap is modified, without restarting pods.

---

## 6. How to Troubleshoot DNS Issues in Kubernetes

### Step 1: Verify CoreDNS Pod Status
Check if CoreDNS pods are running and healthy:
```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns -o wide
```
*Expected: 2/2 pods in `Running` state with 0 restarts.*

### Step 2: Verify the CoreDNS Service
Confirm that the `kube-dns` Service has endpoints and matches the nameserver in `/etc/resolv.conf`:
```bash
kubectl get svc -n kube-system kube-dns
kubectl get endpoints -n kube-system kube-dns
```

### Step 3: Run Diagnostic Query from a Debug Pod
Spawn a temporary interactive curl/dnsutils pod:
```bash
kubectl run dns-test --rm -it --image=infoblox/dnstools --restart=Never -- sh
```
Inside the container, test local cluster resolution and external resolution:
```sh
# Test cluster resolution
nslookup kubernetes.default
nslookup web-service-clusterip.default.svc.cluster.local

# Test external resolution
nslookup github.com

# Inspect local DNS configuration
cat /etc/resolv.conf
```

### Step 4: Inspect CoreDNS Logs
Examine live logs from the CoreDNS pods for errors or forwarding timeouts:
```bash
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=100 -f
```

### Step 5: Common DNS Failure Scenarios and Fixes

| Problem | Root Cause | Solution |
|---|---|---|
| **Cluster names fail; external names work** | CoreDNS cannot contact the Kubernetes API server | Verify CNI overlay network connectivity and API server health |
| **External names fail; cluster names work** | `forward . /etc/resolv.conf` upstream DNS unreachable | Verify host node internet connection and `/etc/resolv.conf` on worker nodes |
| **Sporadic 5-second DNS delays** | Linux kernel `conntrack` race condition on UDP DNS queries | Enable `NodeLocal DNSCache` daemonset or configure TCP DNS |
| **All lookups fail immediately** | CoreDNS pod in `CrashLoopBackOff` due to DNS loop | Check for DNS forwarding loop (`loop` plugin detecting upstream pointing to self) |

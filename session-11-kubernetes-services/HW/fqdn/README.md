# Task 3: Fully Qualified Domain Names (FQDN) in Kubernetes

**Author:** Angel Kumar · 24bcs10011  
**Repository:** [angelkumar427/devops-heros](https://github.com/angelkumar427/devops-heros)

This document explains the concepts, structure, and operational mechanics of Fully Qualified Domain Names (FQDN) in Kubernetes service discovery and networking.

---

## 1. What is an FQDN?

A **Fully Qualified Domain Name (FQDN)** is a complete, unambiguous domain name that specifies the exact location of a host within the hierarchical Domain Name System (DNS) tree. 

In traditional internet DNS, an FQDN ends with a trailing dot representing the DNS root zone (e.g., `api.example.com.`). In Kubernetes, an FQDN unambiguously identifies a specific Service or Pod across namespaces and clusters without relying on client-side search path ambiguities.

---

## 2. Kubernetes Service DNS Architecture

Every Kubernetes cluster runs an internal DNS server (typically **CoreDNS**). When a Service is created, CoreDNS automatically generates corresponding DNS `A` (IPv4) or `AAAA` (IPv6) records that point to the Service's stable Virtual IP (`ClusterIP`).

### Structure of a Kubernetes Service FQDN

```
<service-name>.<namespace>.svc.<cluster-domain>
```

Where:
- `<service-name>`: The name defined in `metadata.name` of the Service manifest.
- `<namespace>`: The Kubernetes namespace where the Service resides (e.g., `default`, `production`, `monitoring`).
- `svc`: Indicates that this DNS record represents a Kubernetes Service object.
- `<cluster-domain>`: The internal cluster domain suffix, standardly `cluster.local` (configurable in `kubelet` and CoreDNS).

---

## 3. Namespace-Based DNS Resolution

Kubernetes uses namespaces as isolation boundaries. Services in the same namespace can communicate using short names, while cross-namespace communication utilizes extended or fully qualified domain names:

1. **Same-Namespace Communication (Short Name):**
   - A client Pod in the `default` namespace connecting to a Service named `web-backend` in the same `default` namespace can simply use:
     ```
     http://web-backend:8080
     ```

2. **Cross-Namespace Communication (Service + Namespace):**
   - A client Pod in the `frontend` namespace connecting to `database-svc` in the `backend` namespace can use:
     ```
     http://database-svc.backend:5432
     ```

3. **Fully Qualified Domain Name (FQDN):**
   - When absolute clarity is required (e.g., to bypass search domain lookup latency or avoid namespace resolution ambiguities), use the complete FQDN:
     ```
     http://database-svc.backend.svc.cluster.local:5432
     ```

---

## 4. How Pod-to-Service Communication Works via DNS

When a Pod is scheduled on a node, `kubelet` automatically populates the Pod container's `/etc/resolv.conf` file with the cluster DNS server IP and the search domains list:

```
nameserver 10.43.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

### Resolution Flow:
When a container in the `default` namespace queries `curl http://web-service:8080`:
1. The standard C resolver checks `/etc/resolv.conf`.
2. Because `web-service` has fewer than 5 dots (`ndots:5`), the resolver appends the first entry in the search list:
   `web-service` + `.default.svc.cluster.local` = `web-service.default.svc.cluster.local`.
3. A DNS query is dispatched to CoreDNS at `10.43.0.10`.
4. CoreDNS matches the record and returns the Virtual IP (e.g., `10.43.190.157`).
5. Subsequent queries for shorter suffixes return `NXDOMAIN` (non-existent domain), which is normal behavior during DNS search path probing.

---

## 5. Pod FQDNs (Headless Services & StatefulSets)

For standard ClusterIP Services, individual Pods do not have dedicated DNS records because all traffic flows through the shared Service VIP. However, when using a **Headless Service** (`spec.clusterIP: None`) with a `StatefulSet`:

### Headless Service FQDN Pattern:
```
<pod-name>.<service-name>.<namespace>.svc.<cluster-domain>
```

### Example:
For a 3-node PostgreSQL cluster running in namespace `database`:
- StateSet name: `postgres`
- Headless Service name: `pg-cluster`
- Individual Pod FQDNs:
  - `postgres-0.pg-cluster.database.svc.cluster.local`
  - `postgres-1.pg-cluster.database.svc.cluster.local`
  - `postgres-2.pg-cluster.database.svc.cluster.local`

This ensures that database primary-replica replication streams have stable, predictable network addresses that survive Pod evictions and rescheduling.

---

## 6. Concrete Examples of Kubernetes FQDNs

| Resource Type | Scope | Example FQDN | Resolves To |
|---|---|---|---|
| **ClusterIP Service** | Default namespace | `web-service-clusterip.default.svc.cluster.local` | Service Virtual IP (`10.43.190.157`) |
| **Cross-Namespace Service** | Prometheus in `monitoring` | `prometheus-k8s.monitoring.svc.cluster.local` | Prometheus Service ClusterIP |
| **CoreDNS System Service** | Kube-system namespace | `kube-dns.kube-system.svc.cluster.local` | CoreDNS VIP (`10.43.0.10`) |
| **StatefulSet Pod** | Elasticsearch replica | `elastic-0.elastic-headless.logging.svc.cluster.local` | Direct Pod IP (`10.42.1.24`) |
| **ExternalName Service** | External database | `ext-db.production.svc.cluster.local` | CNAME record (e.g., `aurora-db.us-east-1.rds.amazonaws.com`) |

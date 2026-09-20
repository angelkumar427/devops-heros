# Task 2: Kubernetes Object Comparison

**Author:** Angel Kumar · 24bcs10011  
**Repository:** [angelkumar427/devops-heros](https://github.com/angelkumar427/devops-heros)

This document provides a comprehensive comparative analysis of core Kubernetes controllers and abstractions, detailing their architecture, operational characteristics, and respective responsibilities.

---

## 1. Deployment vs ReplicaSet

| Dimension | ReplicaSet | Deployment |
|---|---|---|
| **Level of Abstraction** | Low-level Pod controller | High-level declarative workload controller |
| **Primary Purpose** | Maintains a stable set of identical replica Pods running at any given time | Manages declarative updates, rollouts, rollbacks, and lifecycles for ReplicaSets |
| **Direct Pod Management** | Directly creates, monitors, and deletes Pods matching its label selector | Indirect; manages and supervises ReplicaSets, which in turn manage Pods |
| **Scaling** | Directly increments/decrements `spec.replicas` on the ReplicaSet | Modifies `spec.replicas` on the Deployment, which updates the active ReplicaSet |
| **Rolling Updates** | **None.** Updating a ReplicaSet template does not restart existing Pods | **Native.** Automatically orchestrates zero-downtime RollingUpdate or Recreate strategies |
| **Rollback Capability** | Manual recreation or imperative scaling | First-class versioned rollout history with `kubectl rollout undo` |

### Detailed Breakdown

#### Purpose
- **ReplicaSet:** The fundamental building block for self-healing and horizontal pod replication. Its sole purpose is ensuring that exactly `N` Pods matching a label selector exist in a healthy state.
- **Deployment:** A supervisor over ReplicaSets. It abstracts the complexity of software releases, migrations, rolling upgrades, and revision history.

#### Pod Management & Relationship
A Deployment does **not** create Pods directly. Instead, when a Deployment is applied:
1. The Deployment Controller creates a new `ReplicaSet` whose template matches the Deployment specification.
2. The ReplicaSet Controller spawns the target Pods, injecting a unique `pod-template-hash` label (e.g., `app=web, pod-template-hash=84985946cb`).
3. The relationship is strictly hierarchical:
   ```
   Deployment (specifies release intent & rollout strategy)
       │
       └──► Active ReplicaSet (guarantees replica count)
                ├──► Pod 1 (10.42.0.5)
                ├──► Pod 2 (10.42.0.6)
                └──► Pod 3 (10.42.0.7)
   ```

#### Rolling Updates
- When you update container images or environment variables on a Deployment, it creates a **second ReplicaSet** with the new specification.
- In a `RollingUpdate` strategy, the Deployment scales the new ReplicaSet up by 1 replica while simultaneously scaling down the old ReplicaSet by 1 replica, governed by `maxSurge` and `maxUnavailable`.
- The old ReplicaSet is retained at `replicas: 0` to preserve rollback capability.
- If you were managing a raw ReplicaSet, changing the image template does **nothing** to running pods — you would have to manually delete old pods one by one.

---

## 2. Deployment vs DaemonSet vs StatefulSet

| Feature | Deployment | DaemonSet | StatefulSet |
|---|---|---|---|
| **Primary Use Case** | Stateless microservices, REST APIs, web apps | Node-level infrastructure agents (monitoring, logs, CNI) | Stateful applications (PostgreSQL, MongoDB, Kafka, Zookeeper) |
| **Pod Placement / Scheduling** | Distributed across worker nodes by scheduler based on resource availability | Exactly **one** Pod per eligible node (or subset via nodeSelector/tolerations) | Distributed across worker nodes, maintaining ordered indexing (`pod-0`, `pod-1`) |
| **Pod Naming & Identity** | Random hash suffix (e.g., `web-78bf69f78b-x7kqw`), completely ephemeral | Random hash suffix, tied to node presence | Predictable, deterministic ordinal names (`db-0`, `db-1`, `db-2`) |
| **Scaling** | Arbitrary horizontal scaling (`kubectl scale --replicas=N`) | Automatic: scales up when new nodes join the cluster, scales down when nodes leave | Sequential scaling: `N` is created after `N-1` is Ready; terminated in reverse order |
| **Networking** | Pods share a Service VIP (ClusterIP); interchangeable backends | Pods often use `hostPort` or `hostNetwork` to expose node interfaces directly | Requires a **Headless Service** (`clusterIP: None`); each Pod gets an individual DNS FQDN |
| **Storage Architecture** | Ephemeral storage or shared ReadWriteMany (NFS) volumes | HostPath or local node filesystem mounts (`/var/log`, `/proc`, `/sys`) | PersistentVolumeClaimTemplates: each replica gets its own dedicated, persistent volume that re-attaches on restart |
| **Practical Examples** | Nginx, Node.js frontend, FastAPI backend, Go microservices | Fluentd, Logstash, Prometheus Node Exporter, Calico/Flannel CNI agents | Cassandra, Elasticsearch cluster, Redis Sentinel, MySQL replication master/replica |

### Architectural Comparison
- **Deployment:** Assumes Pods are interchangeable and stateless ("cattle"). If `pod-a` crashes, `pod-b` can take its place with zero state synchronization.
- **DaemonSet:** Runs as an ambient background process on every node in the fleet. When a new AWS EC2 worker node registers with the EKS cluster, the DaemonSet controller automatically schedules an instance on that node without manual intervention.
- **StatefulSet:** Designed for stateful clustering ("pets"). Each replica has an immutable network identity (`stateful-app-0.stateful-service.default.svc.cluster.local`) and dedicated persistent storage that retains state across reschedule operations onto different physical worker nodes.

---

## 3. ReplicaSet vs Service

| Criterion | ReplicaSet | Service |
|---|---|---|
| **Core Responsibility** | **Lifecycle & Scale:** Ensures the desired count of running Pod instances exists | **Networking & Routing:** Provides a stable IP, DNS entry, and L4 load balancer to access Pods |
| **Layer of Operation** | Workload / Process management layer | Kernel / Networking layer (kube-proxy, iptables, IPVS) |
| **Key Mechanism** | Reconciliation loop matching `spec.selector` against live Pod labels | `EndpointSlice` controller mapping Service selectors to live Pod IPs |
| **Client Perspective** | Invisible to clients; operates as a Kubernetes backend controller | Front door for clients; stable IP and port that abstracts changing pod instances |
| **Address Stability** | Manages ephemeral Pods with volatile, short-lived IP addresses | Provides an immutable Virtual IP (VIP) and stable DNS hostname |

### Why a Service is Required
Pods in Kubernetes are ephemeral and mortal:
1. When a Pod crashes or a node reboots, the ReplicaSet creates a replacement Pod on another node with a **completely different IP address** (e.g., old Pod was `10.42.0.5`, new Pod is `10.42.0.18`).
2. If client applications connected directly to Pod IPs, every deployment restart, scaling event, or pod eviction would instantly break client connections.
3. A **Service** acts as a stable abstraction:
   - It assigns a virtual IP (`ClusterIP`) that never changes throughout the lifetime of the Service.
   - CoreDNS assigns an internal domain name (`my-service.namespace.svc.cluster.local`).
   - Clients only ever connect to the Service VIP and port.

### How Traffic Reaches Pods
1. **Client initiates request:** A client pod makes an HTTP request to `http://web-service:8080`.
2. **DNS Resolution:** CoreDNS resolves `web-service` to the Service Virtual IP (e.g., `10.43.190.157`).
3. **Kernel Packet Interception:** When the TCP SYN packet leaves the client container, the Linux kernel on the host node encounters netfilter/iptables or IPVS rules programmed by `kube-proxy`.
4. **Destination NAT (DNAT):** The packet destination is rewritten from `10.43.190.157:8080` to one of the healthy endpoint Pod IPs selected by random packet distribution (e.g., `10.42.0.6:80`).
5. **Direct Delivery:** The packet is routed directly across the CNI overlay network to the target Pod container on port 80.

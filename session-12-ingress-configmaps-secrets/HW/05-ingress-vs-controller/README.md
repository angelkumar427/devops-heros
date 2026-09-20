# Task 4: Ingress vs Ingress Controller

**Author:** Angel Kumar · 24bcs10011  
**Repository:** [angelkumar427/devops-heros](https://github.com/angelkumar427/devops-heros)

This document explains the conceptual, operational, and architectural differences between a **Kubernetes Ingress resource** and an **Ingress Controller**.

---

## 1. What is an Ingress?

An **Ingress** is a standard Kubernetes API resource (`kind: Ingress`, `apiVersion: networking.k8s.io/v1`) that defines a declarative set of Layer-7 (HTTP/HTTPS) routing rules.

An Ingress manifest defines:
- **Host routing:** Which incoming HTTP `Host` header maps to which backend (e.g., `api.example.com` vs `store.example.com`).
- **Path routing:** Which URI path prefix routes to which Kubernetes Service (e.g., `/api` -> `backend-svc`, `/` -> `frontend-svc`).
- **TLS termination:** Certificates and Secret references used to decrypt HTTPS connections.

> **Crucial Concept:** An Ingress resource by itself is **pure configuration data stored in etcd**. It does not listen on any network sockets, open ports, or forward network packets. If you apply an Ingress manifest to a cluster that lacks an Ingress Controller, **nothing happens** — the `ADDRESS` field remains blank indefinitely.

---

## 2. What is an Ingress Controller?

An **Ingress Controller** is an active, running application (typically deployed as a Kubernetes Deployment or DaemonSet) that watches the Kubernetes API for `Ingress` resources and actually executes the routing, proxying, and load balancing.

Common Ingress Controllers include:
- **ingress-nginx:** Uses an Nginx reverse proxy engine.
- **Traefik:** Dynamic cloud-native edge router.
- **HAProxy Ingress:** High-performance Layer-4/7 load balancer.
- **AWS Load Balancer Controller:** Provisions and manages AWS Application Load Balancers (ALB) outside the cluster.
- **Envoy-based controllers:** Contour, Emissary-ingress, Istio Ingress Gateway.

The Ingress Controller is exposed to the outside world via a cloud `LoadBalancer` Service or `hostPort`/`NodePort`. When HTTP requests arrive at the controller:
1. It inspects the HTTP headers (`Host`, path, cookies).
2. It matches the request against its internal routing table compiled from cluster `Ingress` objects.
3. It proxies the request directly to the endpoint Pod IPs behind the target Service.

---

## 3. Side-by-Side Comparison

| Feature | Ingress Resource | Ingress Controller |
|---|---|---|
| **What it is** | A Kubernetes API definition (data/rules) | A running process / reverse proxy daemon |
| **Object Type** | `kind: Ingress` | `kind: Deployment` / `DaemonSet` + `Service` |
| **Cluster Component** | Built into Kubernetes API server schema | Third-party or community software (must be installed) |
| **Port / Socket** | None; does not listen on any port | Binds to port 80 and 443 |
| **Packet Forwarding** | Does not touch network traffic | Actively intercepts, proxies, and terminates TLS |
| **Cardinality** | You can create dozens or hundreds across namespaces | Typically 1 or 2 controllers handle traffic for the entire cluster |
| **Failure Mode if Missing** | Ingress stays inert; `ADDRESS` stays `<none>` | Requests never enter the cluster |

---

## 4. Why Both Are Required

The decoupling of **Ingress (specification)** and **Ingress Controller (implementation)** is an intentional design choice of Kubernetes:

1. **Separation of Concerns:**
   - **Application Developers** write simple, standardized Ingress manifests to expose their applications, without worrying about infrastructure details.
   - **Cluster Administrators** choose, configure, and secure the Ingress Controller (e.g., choosing Traefik on k3s, or AWS ALB on AWS EKS).
2. **Economic Efficiency:**
   - In cloud environments, provisioning a Layer-4 `LoadBalancer` Service for every microservice creates a separate AWS/GCP load balancer, resulting in substantial financial costs ($15–$25/month per LB).
   - An Ingress Controller requires only **one** external LoadBalancer for the entire cluster, routing hundreds of services through a single external IP.
3. **Pluggable Architecture:**
   - A cluster can run multiple controllers simultaneously (e.g., `ingressClassName: nginx` for internal services and `ingressClassName: alb` for public internet endpoints).

---

## 5. Practical Example

### The Ingress Resource (`yatri-ingress.yaml`)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: yatri-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  ingressClassName: nginx
  rules:
  - host: yatri.local
    http:
      paths:
      - path: /api(/|$)(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: yatri-backend-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: yatri-frontend-service
            port:
              number: 80
```

### The Ingress Controller Deployment (`ingress-nginx`)
```yaml
# Deployed in namespace: ingress-nginx
# Controller Pod watches Ingress objects matching `ingressClassName: nginx`
# Generates dynamic /etc/nginx/nginx.conf inside the controller pod
# Exposed to outside traffic via:
apiVersion: v1
kind: Service
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: http
  - port: 443
    targetPort: https
```

When a user visits `http://yatri.local/api`:
1. Traffic hits the Ingress Controller's LoadBalancer on port 80.
2. The controller's Nginx worker evaluates the compiled rule for `host: yatri.local` and path `/api`.
3. The controller strips the `/api` prefix (via `rewrite-target: /$2`).
4. The controller proxies the request directly to one of the healthy `yatri-backend-service` Pod IPs on port 80.

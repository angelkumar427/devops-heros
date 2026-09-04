# Docker Networking Task 4 — overlay networks (research + hands-on)

## What an overlay network is

An **overlay network** lets containers on **different Docker hosts** talk to each other by name over an encapsulated tunnel (VXLAN), as if they shared one local network — even when the underlying machines sit on separate subnets, VPCs or data centres. It is the networking layer that makes Docker Swarm work: a service's replicas can be scattered across many machines and still discover and reach each other transparently.

Contrast with the other networks used in this homework:

| Driver | Scope | Spans hosts? | Used in |
|---|---|---|---|
| `bridge` (user-defined) | `local` | no — one daemon only | [Task 1: container-networking](../container-networking/) |
| `host` | `local` | no — shares the host's own stack | [Task 2: host-network](../host-network/) |
| `overlay` | **`swarm`** | **yes** | this task |

## How it actually works

1. **Control plane.** Overlay networks only exist in Swarm mode. The network definition lives in the swarm's raft log on the manager nodes, so every node in the cluster knows about it — hence `Scope: swarm` rather than `local`.
2. **Data plane (VXLAN).** Each host gets a hidden network namespace holding a Linux bridge and a VXLAN interface. A packet from container A to container B on another host is wrapped in a UDP packet (port 4789), sent to the other host's IP, unwrapped, and delivered to B. Containers see a flat L2 network; the physical network only ever sees ordinary UDP.
3. **Service discovery.** Docker's embedded DNS resolves a service name to a **VIP** (virtual IP) that load-balances across replicas, and `tasks.<service>` to the individual replica IPs.
4. **Ingress + routing mesh.** A published service port is reachable on *every* node via the special `ingress` overlay network, which forwards to a node actually running a replica.

## Hands-on (actually run)

Full transcript: [`overlay-demo-output.txt`](./overlay-demo-output.txt).

**Overlay networks require Swarm — proof first:**

```
$ docker network create -d overlay will-fail        # before swarm init
Error response from daemon: This node is not a swarm manager.
```

**Then:**

```bash
docker swarm init
docker network create -d overlay --attachable my-overlay
docker service create --name web-svc --network my-overlay --replicas 3 -p 8089:80 nginx:alpine
```

Note the scope — this is the difference from a bridge network:

```
$ docker network inspect my-overlay --format 'Driver={{.Driver}} Scope={{.Scope}} Attachable={{.Attachable}}'
Driver=overlay Scope=swarm Attachable=true
```

**Service discovery over the overlay:**

```
$ nslookup web-svc            # the service VIP
Address: 10.0.1.2

$ nslookup tasks.web-svc      # every replica, individually
Address: 10.0.1.4
Address: 10.0.1.3
Address: 10.0.1.5
```

**Traffic across the overlay** — a container attached to `my-overlay` reaching the service by name, then each replica by its own overlay IP:

```
$ docker run --rm --network my-overlay alpine wget -qO- http://web-svc/
<title>Welcome to nginx!</title> ...

$ # six requests through the VIP load balancer:
HTTP/1.1 200 OK   HTTP/1.1 200 OK   HTTP/1.1 200 OK
HTTP/1.1 200 OK   HTTP/1.1 200 OK   HTTP/1.1 200 OK

$ # each replica by its overlay IP:
10.0.1.3 -> HTTP/1.1 200 OK
10.0.1.4 -> HTTP/1.1 200 OK
10.0.1.5 -> HTTP/1.1 200 OK
```

## Two honest limitations of this run

**Single node.** This is a one-machine swarm, so all three replicas land on the same host. The overlay control plane, VXLAN interfaces, VIP and DNS are all real and behave identically — but the packets never actually cross a physical network. A second machine would just run `docker swarm join <token>` and replicas would spread across both.

**The routing mesh did not work here.** The published port (`-p 8089:80`) never answered, on macOS *or* from inside the Docker host. Swarm's `ingress` network is unreliable under Colima's VM on macOS. That is a host-platform limitation rather than something about overlay networks, so the overlay was verified via **east-west traffic between containers on the network** (above), which is the capability an overlay actually provides. On a native Linux host the routing mesh works and `curl http://<any-node>:8089` would serve the page from any node in the cluster.

## When you'd reach for one

- Multi-host container deployments without a full Kubernetes install (Swarm services).
- Keeping tiers isolated across a cluster the same way user-defined bridges do on one host.
- Any place you want stable service names and built-in load balancing across machines.

Kubernetes solves the same problem with a CNI plugin (Flannel's VXLAN backend is close to identical in mechanism; Calico can use BGP routing instead of encapsulation).

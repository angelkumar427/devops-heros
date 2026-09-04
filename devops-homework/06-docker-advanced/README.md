# Task 6 — Advanced Docker

Covers two assignment sections: **Dockerfiles & Images** (multi-stage builds) and **Docker Networking & Volumes** (tasks 1–4). Every exercise was actually run — each subfolder holds a full transcript, and web-facing exercises have real browser screenshots.

**Environment:** Docker 29.5.2 on an `aarch64` (Apple Silicon) Docker host, with Colima providing the Linux VM Docker needs on macOS.

---

# Part A — Dockerfiles & Images

| Assignment task | Result | Detail |
|---|---|---|
| Build & run the multi-stage Dockerfile, verify on port 8080 | ✅ | [`multi-stage-build/`](./multi-stage-build/) |
| `.md` with name, enrollment number and evidence | ✅ | [`multi-stage-build/SUBMISSION.md`](./multi-stage-build/SUBMISSION.md) |
| Deploy 3+ application types | ✅ six | [`../05-docker-fundamentals/`](../05-docker-fundamentals/) |

## Multi-stage build — the measured result

```
$ docker images | grep gohello
gohello-multistage    latest    10.5MB
gohello-singlestage   latest     440MB

reduction: 42x smaller (440MB -> 10.5MB)
```

Same running program. The single-stage image ships the entire Go toolchain it only needed at compile time; the multi-stage one copies just the static binary into `scratch` (an empty base image — no shell, no package manager, nothing).

**Required output, on the required port:**

```
$ docker ps
NAMES     IMAGE                STATUS         PORTS
gohello   gohello-multistage   Up 2 seconds   0.0.0.0:8080->8080/tcp

$ curl http://localhost:8080
<h1>Hello World from Docker multi-stage build</h1>
<p>Served from a multi-stage-built Docker image on port 8080.</p>
```

![Multi-stage app on port 8080](./multi-stage-build/screenshots/multistage-app-port-8080.png)

**Understood:** the tools that *build* software are usually not needed to *run* it. `COPY --from=<stage>` is what lets you throw the build environment away and keep only the artefact. `CGO_ENABLED=0` matters here — it produces a fully static binary with no libc dependency, which is the only reason `scratch` works as a base; a dynamically linked binary would still need at least `alpine`.

---

# Part B — Docker Networking & Volumes

| Assignment task | Result | Detail |
|---|---|---|
| T1 — 3 containers, 3 networks, backend on 2 | ✅ | [`container-networking/`](./container-networking/) |
| T2 — Apache2 on the host network, port 80 | ✅ | [`host-network/`](./host-network/) |
| T3 — bind mount into Nginx, edited live | ✅ | [`bind-mounts/`](./bind-mounts/) |
| T4 — research overlay networks | ✅ + live demo | [`overlay-network/`](./overlay-network/) |

## T1 — Three tiers across three networks

`frontend` (nginx) ── `frontend-net` ── `backend` (alpine) ── `db-net` ── `database` (mysql:8.4), with `backend-net` as the third network.

```
$ docker inspect backend --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'
db-net frontend-net              <- the backend is the container on two networks

frontend-net   -> frontend backend
backend-net    ->
db-net         -> database backend
```

| From | To | Shared network? | Result |
|---|---|---|---|
| `frontend` | `backend:5000` | yes | ✅ `backend-tier-OK` |
| `backend` | `database:3306` | yes | ✅ DNS → `172.20.0.2`, TCP open |
| `frontend` | `database:3306` | **no** | ❌ `nc: bad address 'database'` |
| container on `backend-net` | anything | **no** | ❌ nothing resolves |

**Understood:** the failures prove the design as much as the successes. Docker's embedded DNS only resolves container names *within a shared network*, so isolation is enforced at name-resolution time — before a packet is even sent. Putting the backend on two networks makes it the **only** path from the frontend tier to the database, which is exactly why you'd lay it out this way instead of putting everything on one network.

## T2 — Apache2 with `--network host` on port 80

```
$ docker run -d --name apache-host --network host httpd:2.4

$ docker ps
NAMES         IMAGE       STATUS         PORTS   NETWORKS
apache-host   httpd:2.4   Up 3 seconds           host      <- no -p, no ports column

$ curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://localhost:80/
HTTP 200

$ curl -sS http://localhost:80/
<html><head><title>It works! Apache httpd</title></head><body><p>It works!</p></body></html>
```

![Apache2 on host network port 80](./host-network/screenshots/apache2-host-network-port80.png)

**Understood:** in bridge mode a container gets its own namespace and IP and needs `-p` to be reachable. With `--network host` there's no separate namespace, no NAT and no `-p` — whatever the process binds inside the container *is* that port on the host. The clinching proof is that the container and the host report the **same hostname** (`colima`), because they are the same network namespace.

## T3 — Bind mount, edited live

```
$ echo "<h1>Hello students</h1>" > site/index.html
$ docker run -d --name bindmount-demo -p 8088:80 -v "$PWD/site":/usr/share/nginx/html:ro nginx:alpine

$ curl -sS http://localhost:8088/
<h1>Hello students</h1>
```

Then edit the file **on the host** and re-request, with no restart:

```
$ echo "<h1>Hello students - edited live on the host</h1>" > site/index.html
$ curl -sS http://localhost:8088/
<h1>Hello students - edited live on the host</h1>

$ docker inspect bindmount-demo --format 'StartedAt={{.State.StartedAt}} Restarts={{.RestartCount}}'
StartedAt=2026-09-03T18:16:35Z Restarts=0
```

| Before the edit | After the edit |
|---|---|
| ![before](./bind-mounts/screenshots/bind-mount-1-before-edit.png) | ![after](./bind-mounts/screenshots/bind-mount-2-after-host-edit.png) |

`:ro` also verified — the container cannot write back:

```
$ docker exec bindmount-demo sh -c "echo hacked > /usr/share/nginx/html/index.html"
sh: can't create /usr/share/nginx/html/index.html: Read-only file system
```

**Understood:** `Restarts=0` with an unchanged `StartedAt` is the proof that matters — the container is reading the host's actual file on every request, not a copy taken at start-up. That's the difference from a named volume (Docker-managed storage, good for database files) and it's why bind mounts are the standard way to live-edit source during development. Bind mounts are bidirectional by default, so `:ro` is worth adding whenever the container has no business writing back.

## T4 — Overlay networks

```
$ docker network create -d overlay will-fail       # before swarm init
Error response from daemon: This node is not a swarm manager.

$ docker swarm init
$ docker network create -d overlay --attachable my-overlay
$ docker network inspect my-overlay --format 'Driver={{.Driver}} Scope={{.Scope}}'
Driver=overlay Scope=swarm                          <- "swarm", not "local"

$ docker service create --name web-svc --network my-overlay --replicas 3 -p 8089:80 nginx:alpine
$ nslookup web-svc          -> 10.0.1.2             (one VIP, load-balanced)
$ nslookup tasks.web-svc    -> 10.0.1.3, .4, .5     (each replica)

$ docker run --rm --network my-overlay alpine wget -qO- http://web-svc/
<title>Welcome to nginx!</title> ...
10.0.1.3 -> HTTP/1.1 200 OK
10.0.1.4 -> HTTP/1.1 200 OK
10.0.1.5 -> HTTP/1.1 200 OK
```

**Understood:** an overlay lets containers on *different hosts* talk by name over a VXLAN tunnel, which is what makes Swarm services possible. The giveaway is `Scope: swarm` — the network definition lives in the swarm's raft log, so every node knows about it, unlike a `local`-scope bridge. Service discovery has two forms worth knowing: the service name resolves to a single **VIP** that load-balances, while `tasks.<service>` resolves to the individual replicas.

---

## Two limitations documented rather than hidden

1. **`--network host` shares the VM's namespace, not macOS's.** On macOS the Docker host *is* the Colima VM, so port 80 is bound there; the screenshot was taken through an SSH tunnel into the VM. On native Linux there's no VM and `curl http://localhost:80` works directly. ([detail](./host-network/README.md#platform-note-important-for-reproducing-this))
2. **Swarm's routing mesh doesn't work under Colima.** The published port `8089` never answered, from macOS or inside the VM. That's a host-platform limitation, not an overlay one, so the overlay was verified by container-to-container traffic over it — which is the capability an overlay actually provides. ([detail](./overlay-network/README.md#two-honest-limitations-of-this-run))

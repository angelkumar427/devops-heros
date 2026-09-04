# Docker Networking Task 2 — Apache2 on the host network, port 80

By default a container gets its **own network namespace** — its own virtual interface, its own IP on a bridge — and you must publish ports with `-p host:container` to reach anything inside it. With `--network host` the container **shares the Docker host's network namespace directly**: no isolation, no virtual interface, no NAT, no `-p` needed. Whatever port the process binds inside the container *is* that port on the host.

Full transcript: [`host-network-demo-output.txt`](./host-network-demo-output.txt).

## Setup

```bash
docker pull httpd:2.4
docker run -d --name apache-host --network host httpd:2.4
curl http://localhost:80/
```

## Bridge vs host, side by side

**Bridge (default)** — needs an explicit publish, and the container has its own IP:

```
$ docker run -d --name apache-bridge -p 8086:80 httpd:2.4
$ docker port apache-bridge
80/tcp -> 0.0.0.0:8086
$ docker inspect apache-bridge --format '{{.NetworkSettings.IPAddress}}'
172.17.0.2
```

**Host mode** — no `-p`, no ports column, no IP of its own:

```
$ docker run -d --name apache-host --network host httpd:2.4
$ docker ps
NAMES         IMAGE       STATUS         PORTS   NETWORKS
apache-host   httpd:2.4   Up 3 seconds           host

$ docker inspect apache-host --format 'NetworkMode={{.HostConfig.NetworkMode}}'
NetworkMode=host
```

## Apache answering on port 80

```
$ curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://localhost:80/
HTTP 200

$ curl -sS http://localhost:80/
<html><head><title>It works! Apache httpd</title></head>
<body><p>It works!</p></body></html>

$ ss -tlnp | grep ':80 '
LISTEN 0  511  *:80  *:*
```

The clearest proof that the namespace really is shared — the container and the Docker host report the **same hostname**, because they are the same network namespace:

```
$ docker exec apache-host hostname
colima
$ <the Docker host>: hostname
colima
```

## Screenshot

![Apache2 on the host network, port 80](./screenshots/apache2-host-network-port80.png)

## Platform note (important for reproducing this)

This was run on macOS, where Docker itself runs inside a Linux VM (Colima). `--network host` shares the network namespace of **the Docker host**, which on macOS is that VM — not macOS itself. So port 80 is bound on the VM, and every check above is run from inside it. The screenshot was taken through an SSH tunnel (`ssh -L 8087:127.0.0.1:80` into the VM) so a macOS browser could reach the VM's port 80.

On a native Linux Docker host there is no VM in between: `--network host` binds port 80 on the machine itself and `curl http://localhost:80` works directly.

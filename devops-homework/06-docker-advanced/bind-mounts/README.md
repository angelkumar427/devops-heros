# Docker Networking Task 3 — bind mount a host folder into Nginx

`-v <host-path>:<container-path>` (a **bind mount**) makes a directory on the host and a directory inside the container point at the *exact same files on disk* — not a copy taken at container start. Edit either side and the other sees it instantly: no rebuild, no restart.

This differs from a **named volume** (`docker volume create`, then `-v myvol:/path`), which is storage Docker manages itself — good for persisting data like a database's files. A bind mount is specifically for "mirror this host directory into the container", which is what you want for live-editing source or static assets.

Full transcript: [`bind-mount-demo-output.txt`](./bind-mount-demo-output.txt).

## Setup

```bash
mkdir -p site
echo "<h1>Hello students</h1>" > site/index.html

docker run -d --name bindmount-demo -p 8088:80 \
  -v "$PWD/site":/usr/share/nginx/html:ro nginx:alpine

curl http://localhost:8088/
```

The mount as Docker sees it:

```
$ docker inspect bindmount-demo --format '{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}} (rw={{.RW}}){{end}}'
bind /.../bind-mounts/site -> /usr/share/nginx/html (rw=false)
```

## The live-reload result

**1. Initial content** ([`site/index.html`](./site/index.html)):

```
$ curl -sS http://localhost:8088/
<h1>Hello students</h1>
```

![Before the edit](./screenshots/bind-mount-1-before-edit.png)

**2. Edit the file on the host** — the container is never touched:

```
$ echo "<h1>Hello students - edited live on the host</h1>" > site/index.html
```

**3. The change is served immediately, with no restart:**

```
$ curl -sS http://localhost:8088/
<h1>Hello students - edited live on the host</h1>

$ docker inspect bindmount-demo --format 'StartedAt={{.State.StartedAt}} Restarts={{.RestartCount}}'
StartedAt=2026-09-03T18:16:35Z Restarts=0
```

![After the host edit](./screenshots/bind-mount-2-after-host-edit.png)

`Restarts=0` and an unchanged `StartedAt` are the proof that nothing was restarted — the container is reading the host's file on every request.

## `:ro` — read-only from the container side

The mount is made read-only, so the container cannot tamper with the host's files:

```
$ docker exec bindmount-demo sh -c "echo hacked > /usr/share/nginx/html/index.html"
sh: can't create /usr/share/nginx/html/index.html: Read-only file system
(exit 1)

$ curl -sS http://localhost:8088/        # host content untouched
<h1>Hello students - edited live on the host</h1>
```

Drop `:ro` and writes from inside the container would land on the host directory too — bind mounts are bidirectional by default, which is worth knowing before mounting anything sensitive.

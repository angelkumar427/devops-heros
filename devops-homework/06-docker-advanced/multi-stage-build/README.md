# Multi-stage builds

A multi-stage `Dockerfile` uses more than one `FROM` in the same file. Each `FROM` starts a fresh, independent stage; later stages can `COPY --from=<stage>` selected files out of an earlier one. Only the **final** stage becomes the image you actually get — everything from earlier stages (compilers, source, package caches, headers) is left behind unless explicitly copied forward.

Why it matters: the tools needed to *compile* something are usually not needed to *run* it, and they are often enormous.

## This demo

A tiny Go HTTP server ([`main.go`](./main.go)) that serves the string the assignment requires — **`Hello World from Docker multi-stage build`** — on **port 8080**, built two ways:

- **[`Dockerfile.single-stage`](./Dockerfile.single-stage)** — one stage. Compiles with the full `golang:1.22-alpine` toolchain and ships that entire toolchain in the final image, even though it is never needed again.
- **[`Dockerfile`](./Dockerfile)** (multi-stage) — stage 1 (`build`) compiles a fully static binary (`CGO_ENABLED=0`); stage 2 starts from `scratch` (a literally empty base image) and copies in **only the compiled binary**. No shell, no package manager, no Go toolchain in the final image.

## Measured result

| Image | Base of final stage | Size on disk |
|---|---|---|
| `gohello-singlestage` | `golang:1.22-alpine` | **440 MB** |
| `gohello-multistage` | `scratch` | **10.5 MB** |

**42x smaller**, same running program. Full transcript: [`build-comparison-output.txt`](./build-comparison-output.txt).

## Build, run and verify

```bash
docker build -f Dockerfile.single-stage -t gohello-singlestage .
docker build -f Dockerfile -t gohello-multistage .
docker images | grep gohello

docker run -d --name gohello -p 8080:8080 gohello-multistage
docker ps
curl http://localhost:8080
```

`docker ps` confirming the container on port 8080:

```
NAMES     IMAGE                STATUS         PORTS
gohello   gohello-multistage   Up 2 seconds   0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp
```

`curl http://localhost:8080`:

```html
<!doctype html>
<html>
<head><title>Multi-stage build</title></head>
<body>
<h1>Hello World from Docker multi-stage build</h1>
<p>Served from a multi-stage-built Docker image on port 8080.</p>
</body>
</html>
```

## Screenshot

The application running in a browser on port 8080:

![Multi-stage app on port 8080](./screenshots/multistage-app-port-8080.png)

## Why `scratch` works here

`CGO_ENABLED=0` makes Go emit a fully static binary with no libc dependency, so it needs nothing from the base image — not even a dynamic loader. That is what allows the final stage to be empty. A binary linked against libc would need at least `alpine` or `distroless` as its base instead.

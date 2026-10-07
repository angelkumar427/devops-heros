# Mini Project — Layered-Fault Troubleshooting Challenge

**Session 14 homework** · Angel Kumar · 24bcs10011

> Cluster: k3s `v1.35.0+k3s1`, node `colima`. Raw output: [`transcript.txt`](./transcript.txt).
> Original brief: [`ASSIGNMENT-BRIEF.md`](./ASSIGNMENT-BRIEF.md).

The brief's "break" step is a single bad-image pod, which duplicates [scenario 2](../03-imagepullbackoff/). To make it a real challenge, [`break.sh`](./break.sh) introduces **three faults at once** — the way production incidents actually look:

| # | Fault | Kind |
|---|---|---|
| 1 | A pod with a non-existent image (the provided `broken-pod.yaml`) | **Red herring** — loud, real, but unrelated |
| 2 | Service selector typo: `app=troubleshooting` | **Real** — black-holes all traffic |
| 3 | Service `targetPort: 8080` (nginx listens on 80) | **Real** — only visible after #2 is fixed |

![Mini project](./mini-project.png)

---

## Deploy → Observe

```
$ kubectl apply -f deployment.yaml -f service.yaml
$ curl troubleshooting-service
  <title>Welcome to nginx!</title>           <- healthy baseline
```

## Break

```
$ ./break.sh
pod/project-broken-pod created
service/troubleshooting-service patched
```

## Investigate — "the app is down"

```
$ curl troubleshooting-service
  wget: can't connect to remote host (10.43.226.82): Connection refused

$ kubectl get pods
  project-broken-pod                     0/1   ErrImagePull     <- loudest thing on screen
  troubleshooting-app-9d7b5cd79-gkkb7    1/1   Running
  troubleshooting-app-9d7b5cd79-mp9p6    1/1   Running
```

The obvious move is to chase the `ErrImagePull`. **Checking whether it can matter first:**

```
$ kubectl get pod project-broken-pod --show-labels
  labels: <none>
```

No labels — **no Service can select it**, so it cannot cause this outage. A red herring: worth fixing, not the cause. The app pods are `Running` and `Ready`, so the fault is on the path between client and pods:

```
$ kubectl get endpoints troubleshooting-service
   troubleshooting-service <none>

$ kubectl get svc troubleshooting-service -o jsonpath='{.spec.selector}'
  {"app":"troubleshooting"}

pod label: app=troubleshooting-app
```

## Root cause #1 — selector typo

`app=troubleshooting` vs `app=troubleshooting-app`. Fixed:

```
$ kubectl get endpoints troubleshooting-service
   troubleshooting-service 10.42.0.101:8080,10.42.0.102:8080

$ curl troubleshooting-service
  wget: can't connect to remote host (10.43.226.82): Connection refused
```

**Endpoints are populated now — and it still fails. Fixing #1 revealed #2.** The clue is right there in the endpoint list: `:8080`.

```
$ kubectl get svc troubleshooting-service -o jsonpath='{.spec.ports[0]}'
  {"port":80,"protocol":"TCP","targetPort":8080}

$ kubectl exec deploy/troubleshooting-app -- cat /proc/net/tcp     # LISTEN sockets, decoded
  listening on port 80
```

The nginx image ships neither `ss` nor `netstat`, so the kernel's socket table was read directly to prove what the container actually listens on.

## Root cause #2 — targetPort mismatch

The Service forwards to 8080; nginx listens on 80. Fixed `targetPort: 80`, then cleaned up the red herring too.

## Verify

```
$ kubectl get endpoints troubleshooting-service
   troubleshooting-service 10.42.0.101:80,10.42.0.102:80

$ curl troubleshooting-service
  <title>Welcome to nginx!</title>

$ kubectl get pods
  troubleshooting-app-9d7b5cd79-gkkb7   1/1   Running
  troubleshooting-app-9d7b5cd79-mp9p6   1/1   Running
```

---

## What I understood

- **The loudest error is not necessarily the cause.** `ErrImagePull` dominated `kubectl get pods` but had no labels and so could not touch the Service. Asking *"can this thing even affect the symptom?"* before chasing it saved the investigation.
- **Faults mask each other.** The targetPort bug was invisible while the selector bug existed — with no endpoints there's no port to be wrong. In a real incident, "I fixed it and it still doesn't work" usually means *there was more than one problem*, not that the first fix was wrong.
- **Read the output you already have.** The endpoints line `10.42.0.101:8080` contained the answer to fault #2 before any further command was run.
- **Work the path from the outside in:** symptom (curl) → endpoints → selector → ports → what the container actually listens on.

## Files

| File | Purpose |
|---|---|
| [`deployment.yaml`](./deployment.yaml) · [`service.yaml`](./service.yaml) | The healthy application |
| [`broken-pod.yaml`](./broken-pod.yaml) | The provided bad-image pod (the red herring) |
| [`break.sh`](./break.sh) | Introduces all three faults |
| [`ASSIGNMENT-BRIEF.md`](./ASSIGNMENT-BRIEF.md) | Original challenge brief |

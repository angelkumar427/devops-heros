# Session 13 — Kubernetes Storage, HPA & Probes

**Homework submission** · Angel Kumar · 24bcs10011

> **Cluster:** k3s `v1.35.0+k3s1`, single node (`colima`), 4 CPU / 8 GB, on a Colima VM
> (macOS/Apple Silicon). Default StorageClass `local-path`; `metrics-server` running.
> Every output and screenshot was captured from a real run.

## Contents

| # | Task | What was proved | Folder |
|---|---|---|---|
| 1 | **Volumes** | emptyDir wiped on pod deletion, hostPath written straight to the node, PVC data survived — plus a real binding trap | [`01-kubernetes-volumes/`](./01-kubernetes-volumes/) |
| 2 | **HPA** | Scaled **1 → 5** under load and back to **1**, with the 5-minute stabilization window visible | [`02-hpa/`](./02-hpa/) |
| 3 | **Mini project** | PVC + HPA + startup/readiness/liveness probes in one namespace; data survived pod replacement | [`03-mini-project/`](./03-mini-project/) |

## Evidence at a glance

| Volumes — the PV/PVC binding trap | HPA — scaling up under load |
|---|---|
| ![vol](./01-kubernetes-volumes/02-pv-pvc-binding.png) | ![up](./02-hpa/01-hpa-scale-up.png) |

| HPA — scaling down after the 5-min window | Mini project — all three pillars |
|---|---|
| ![down](./02-hpa/02-hpa-scale-down.png) | ![mp](./03-mini-project/01-mini-project.png) |

## Three findings worth highlighting

**1. Omitting `storageClassName` is not the same as setting it to `""`.** A PVC that leaves the field out gets the cluster's **default** StorageClass injected, so it silently ignores a hand-created PV and dynamically provisions a new volume instead. The symptom is a `Pending` PVC sitting next to an `Available` PV, with no error anywhere. The fix is an explicit empty string. [Details](./01-kubernetes-volumes/#3-pv--pvc--and-a-trap-worth-knowing)

**2. HPA scale-up and scale-down are deliberately asymmetric.** CPU dropped to 0% within a minute of removing load, but replicas stayed at 5 for another **five minutes** — the downscale stabilization window, which stops a brief lull from destroying capacity you're about to need. [Details](./02-hpa/#scaling-down)

**3. The obvious load generator doesn't work.** A busybox `wget` loop spawns a process per request, so the *generators* saturated the node's CPU (the API server even timed out) while nginx sat near-idle at 9%. Swapping to ApacheBench took the target to **198%** instantly. A load test proves nothing until you've confirmed the generator isn't the bottleneck. [Details](./02-hpa/#a-load-generator-that-actually-works)

## One thing the manifests don't tell you

The mini project mounts a **`ReadWriteOnce`** PVC into a Deployment that the HPA can scale to 5 replicas. On this single-node cluster that works fine. On a real multi-node cluster it would break the moment a new replica landed on a different node, because RWO allows exactly one node to mount the volume. The production answers are RWX storage, a StatefulSet with per-pod volumes, or keeping shared state in a database. Worth knowing before copying the pattern.

## A note on the screenshots

Terminal images are the **real, unedited output** of the commands shown, rendered to PNG for readability. Every line also appears as text in the READMEs, so nothing depends on reading an image.

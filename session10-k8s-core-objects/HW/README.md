# Session 10 — Kubernetes Pods, ReplicaSets & Deployments

**Homework submission** · Angel Kumar · 24bcs10011

> **Cluster:** k3s `v1.35.0+k3s1`, single node (`colima`), in a Colima VM on macOS/Apple Silicon.
> Every output and screenshot here was captured from a real run.

## Contents

| Topic | What was proved | Folder |
|---|---|---|
| **Core objects** | All five deployed together; ReplicaSet self-healing demonstrated by deleting a pod | [`core-objects/`](./core-objects/) |
| **Pod lifecycle** | 12 pods in 12 different states, and the `STATUS` ≠ `phase` distinction proved with real data | [`pod-lifecycle/`](./pod-lifecycle/) |
| **Rolling update** | Two ReplicaSets trading places live; rollback swapped them back without creating anything | [`01-rolling-update/`](./01-rolling-update/) |
| **Blue-green** | One selector edit moved all traffic; `Server` header went 1.24 → 1.25 → 1.24 | [`02-blue-green/`](./02-blue-green/) |
| **Canary** | 200 requests measured **180/20** — exactly the 9:1 pod ratio | [`03-canary/`](./03-canary/) |
| **Recreate** | Downtime captured: `readyReplicas` hit **0** mid-rollout | [`04-recreate/`](./04-recreate/) |
| **Troubleshooting** | Selector mismatch rejected at admission; broken image stalled a rollout with 3/3 still available | [`troubleshooting/`](./troubleshooting/) |

## The four deployment strategies, compared

| Strategy | Downtime | Extra capacity | Versions live at once | Rollback speed |
|---|---|---|---|---|
| **Recreate** | **Yes** (measured) | None | Never | Slow |
| **Rolling update** | No | `maxSurge` | Briefly, mixed | Fast |
| **Blue-green** | No | **2x** | Both, one serving | **Instant** |
| **Canary** | No | Small | Deliberately, by ratio | Fast |

The choice is really one question: **can v1 and v2 safely run at the same time?** If not (breaking schema change, `ReadWriteOnce` volume), it's Recreate. If yes, the rest is a trade between spare capacity and how much risk you want to take at once.

## Three results worth highlighting

**1. The canary split was exactly 90/10 without configuring any percentage.** 200 requests returned 180 from `nginx/1.24` and 20 from `nginx/1.25`. Nothing sets that ratio — it falls out of kube-proxy balancing across 10 endpoints where 1 belongs to the canary. That also exposes the limitation: with plain Services the granularity *is* the replica count.

**2. `STATUS` in `kubectl get pods` is not the pod phase.** The crashlooping pod's phase was `Running`; the `ImagePullBackOff` pod's phase was `Pending`. There are only five phases — `CrashLoopBackOff` and `ImagePullBackOff` are container waiting reasons layered on top.

**3. A broken image did not cause an outage.** Rolling out a non-existent tag left `3/3 AVAILABLE` with the original pods untouched, because the default `maxUnavailable: 25%` rounds **down to 0** at 3 replicas. The rollout stalled instead of degrading the service.

## Two environment findings

- **`mysql:5.7` cannot run on Apple Silicon** — `no matching manifest for linux/arm64/v8`. The tag was never published for arm64; `mysql:8.4` was. Documented with both manifests in [`core-objects/`](./core-objects/#a-real-failure-worth-keeping-mysql57-wont-run-here).
- Several manifests use resource requests sized for a larger node; the `Pending` pod in the lifecycle set requests 9 GiB deliberately, which is what makes it unschedulable and is exactly the point of that exercise.

## A note on the screenshots

Terminal images are the **real, unedited output** of the commands shown, rendered to PNG for readability. Every line also appears as text in the READMEs, so nothing depends on reading an image.

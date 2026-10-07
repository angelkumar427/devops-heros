# OOMKilled — and the bug hiding behind it

**Session 14 homework** · Angel Kumar · 24bcs10011

> Cluster: k3s `v1.35.0+k3s1`, node `colima`. Full raw output: [`transcript.txt`](./transcript.txt).

![OOMKilled — and the bug hiding behind it](./oomkilled.png)

## 1. Identify

```
NAME                   READY   STATUS             RESTARTS      NODE
fail-5-oomkilled-pod   0/1     CrashLoopBackOff   1 (12s ago)   colima
```

It *looks* like an ordinary crashloop. It isn't.

## 2. Investigate

```
$ kubectl describe pod fail-5-oomkilled-pod | grep -A3 "Last State"
    Last State:  Terminated
      Reason:    OOMKilled
      Exit Code: 137

$ kubectl get pod ... -o jsonpath='{.spec.containers[0].resources}'
{"limits":{"memory":"20Mi"},"requests":{"memory":"20Mi"}}
```

## 3. Root cause

The program allocates 100 × 10 MB ≈ 1000 MB against a **20Mi** limit; the kernel OOM-killer terminates it the instant it crosses the line. **Exit code 137 = 128 + 9 (SIGKILL)** — the process didn't fail, it was *killed*. That's what separates this from the [CrashLoopBackOff](../02-crashloopbackoff/) case (exit 1). `kubectl logs` helps little: the process dies mid-allocation.

## 4. Fix

Raise the limit to the real working set (`1200Mi`).

> In production the first question is whether the usage is legitimate or a leak. Raising a limit only fixes the former; this demo allocates on purpose.

## 5. Verify

```
NAME                   READY   STATUS      RESTARTS
fail-5-oomkilled-pod   0/1     Completed   0
  reason=Completed exitCode=0
```

### A second bug, found while verifying

The first fix (memory only) left **`RESTARTS` climbing on a pod that was succeeding**. Checking `lastState` showed `Completed`, exit `0` — not OOM. The manifest sets no `restartPolicy`, so it defaults to **`Always`**, and Kubernetes restarted the script after every *successful* run. A one-shot task needs `restartPolicy: OnFailure` (or `Never`) — or better, to be a **Job**. [`fixed.yaml`](./fixed.yaml) carries both fixes; after them, `RESTARTS` stayed at `0`.

This is the most useful lesson in the set: **verifying a fix properly can surface a second fault the first one was masking.**

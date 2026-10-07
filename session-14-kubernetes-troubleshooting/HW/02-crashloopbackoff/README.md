# CrashLoopBackOff

**Session 14 homework** · Angel Kumar · 24bcs10011

> Cluster: k3s `v1.35.0+k3s1`, node `colima`. Full raw output: [`transcript.txt`](./transcript.txt).

![CrashLoopBackOff](./crashloopbackoff.png)

## 1. Identify

The pod starts, its process exits, Kubernetes restarts it, it exits again — with an exponentially growing delay between attempts.

```
NAME         READY   STATUS   RESTARTS      AGE
crash-demo   0/1     Error    2 (38s ago)   40s
```

## 2. Investigate

```
$ kubectl describe pod crash-demo | grep -A4 "Last State"
    Last State:  Terminated
      Reason:    Error
      Exit Code: 1

$ kubectl logs crash-demo
Application starting...
Something went wrong!

$ kubectl logs crash-demo --previous
unable to retrieve container logs for docker://623e44d8...
```

**A nuance worth knowing.** Textbooks say "use `--previous` for crashloops", and here it *failed*. While the pod waits out its back-off, the **current** container *is* the one that just died — so plain `kubectl logs` shows the crash. `--previous` asks for the one *before* that, which kubelet had already garbage-collected (it keeps only one dead container per pod, confirmed with `docker ps -a` on the node). `--previous` is the right tool once the container has been restarted and is running or crashing again.

## 3. Root cause

The command runs `exit 1`. With `restartPolicy: Always` Kubernetes keeps restarting it. **The image, node and network are all fine — the application itself is the problem.** Exit code `1` means the app failed on its own; compare `137` in [OOMKilled](../06-oomkilled/), which means it was killed from outside.

## 4. Fix

Replace the failing command with the real long-running workload ([`fixed-pod.yaml`](./fixed-pod.yaml)).

## 5. Verify

```
NAME         READY   STATUS    RESTARTS   AGE
crash-demo   1/1     Running   0          16s

$ kubectl logs crash-demo
Application starting...
Application is healthy
```

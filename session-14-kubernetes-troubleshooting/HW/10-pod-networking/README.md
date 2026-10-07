# Pod networking — NetworkPolicy

**Session 14 homework** · Angel Kumar · 24bcs10011

> Cluster: k3s `v1.35.0+k3s1`, node `colima`. Full raw output: [`transcript.txt`](./transcript.txt).

![Pod networking — NetworkPolicy](./networkpolicy.png)

## 1. Identify

Baseline: two client pods reach the web Service. After a policy is applied, **both are refused**:

```
  client   -> wget: can't connect to remote host (10.43.154.252): Connection refused
  intruder -> wget: can't connect to remote host (10.43.154.252): Connection refused
```

Pods `Running`, Service has endpoints, DNS resolves — every layer above the network looks healthy. That's what makes this one hard.

## 2. Investigate

```
$ kubectl get networkpolicy
NAME           POD-SELECTOR   AGE
web-deny-all   app=web        8s

$ kubectl describe networkpolicy web-deny-all
  PodSelector:     app=web
  Allowing ingress traffic:
    <none> (Selected pods are isolated for ingress connectivity)
```

## 3. Root cause

A NetworkPolicy selects `app=web` and lists **no** ingress rules. The moment *any* policy selects a pod, all ingress not explicitly allowed is dropped.

> **The symptom depends on the CNI.** k3s's kube-router **REJECTs** blocked packets, so this shows as an instant *Connection refused*. CNIs that silently **DROP** (Calico, by default) show a *timeout* for exactly the same problem. Know which you have before reading too much into the error.

## 4. Fix

Add an allow rule for exactly the intended traffic — ingress from `role=client` on TCP 80 ([`allow-from-client.yaml`](./allow-from-client.yaml)).

## 5. Verify

```
  client   -> <title>Welcome to nginx!</title>
  intruder -> wget: can't connect to remote host (10.43.154.252): Connection refused
```

Policies are **additive**: deny-all plus one allow rule gives exactly the intended access — the client gets through, the intruder is still refused.

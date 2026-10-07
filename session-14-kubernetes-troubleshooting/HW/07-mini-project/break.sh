#!/usr/bin/env bash
# Introduces three faults at once, the way real incidents usually look:
#   1. a loud but UNRELATED red herring  (the provided broken pod)
#   2. a Service selector typo          (no endpoints -> traffic black-holed)
#   3. a wrong Service targetPort       (only visible once #2 is fixed)
kubectl apply -f broken-pod.yaml
kubectl patch svc troubleshooting-service --type merge \
  -p '{"spec":{"selector":{"app":"troubleshooting"},"ports":[{"port":80,"targetPort":8080}]}}'

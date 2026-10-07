# Security controls

| Control | Tool | Where | Gate |
|---|---|---|---|
| SAST | Bandit | CI, `security/bandit.yaml` | Fails on MEDIUM+ |
| SCA | pip-audit | CI | Fails on any known vulnerability |
| Secret scanning | Gitleaks | CI, `security/.gitleaks.toml` | Fails on any finding |
| Image scanning | Trivy | CI, `security/trivy.yaml` | Fails on fixable HIGH/CRITICAL |
| Security gate | workflow logic | CI | Image is only pushed if all four pass |

Runtime hardening (in the Helm chart): non-root UID 10001, read-only root filesystem,
all capabilities dropped, no privilege escalation, `RuntimeDefault` seccomp profile.

Secrets: the chart's `values.yaml` carries a clearly-labelled **demo** token. Production sets
`secret.existingSecret` to a Secret managed by Sealed Secrets or External Secrets, so no
credential is ever committed to Git.

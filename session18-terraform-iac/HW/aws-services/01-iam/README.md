# 01 — IAM: Identity and Access Management (Governance)

**Session 18 homework** · Angel Kumar · 24bcs10011

## What is IAM?

IAM is the AWS service that decides **who can do what to which resource**. Every single AWS API call — from the console, the CLI, Terraform, or an application — is authenticated (*who are you?*) and then authorised against IAM policies (*are you allowed to do this?*). It is global (not per-region) and free.

If IAM is wrong, nothing else about an AWS account's security matters.

## The building blocks

| Concept | What it is | Typical use |
|---|---|---|
| **Root user** | The account's original identity, with unrestricted power | Lock it away: MFA on, no access keys, used only for the handful of tasks that require it |
| **User** | A long-lived identity for one person or system, with a password and/or access keys | Humans, increasingly replaced by SSO (IAM Identity Center) |
| **Group** | A collection of users; policies attached to it apply to every member | `developers`, `readonly-auditors` |
| **Role** | An identity with **no long-term credentials**. Anyone (or anything) trusted can *assume* it and receive **temporary** credentials | EC2 instances, Lambda functions, CI pipelines, cross-account access |
| **Policy** | A JSON document listing what is allowed or denied | Attached to users, groups or roles |

### Users vs roles — the most important distinction

A **user** has *permanent* credentials (access key + secret). If they leak, they work until someone notices and rotates them.

A **role** hands out credentials that **expire automatically** (typically within an hour). An EC2 instance with a role, or a GitHub Actions pipeline using OIDC to assume a role, never holds a long-lived secret at all. **Prefer roles wherever a machine needs access.**

## Policies

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::devops-heros-dev-*/*"
    }
  ]
}
```

| Element | Meaning |
|---|---|
| `Effect` | `Allow` or `Deny` |
| `Action` | API operations, e.g. `s3:GetObject` (wildcards allowed) |
| `Resource` | ARNs the statement applies to |
| `Condition` | Optional extra rules — source IP, MFA present, tags, time |

**Policy types:** *AWS-managed* (maintained by AWS, often too broad), *customer-managed* (yours, reusable), *inline* (embedded in one identity). Plus *resource-based* policies attached to the resource itself (an S3 bucket policy), and *trust policies* that say who may assume a role.

## Permissions — how AWS evaluates a request

```
1. Is there an explicit DENY anywhere?          -> DENY  (always wins)
2. Is there an explicit ALLOW that matches?     -> ALLOW
3. Otherwise                                    -> DENY  (implicit deny by default)
```

**Everything is denied unless something allows it, and an explicit deny beats any allow.** That second rule is what makes guardrails like Service Control Policies effective.

## Least privilege

Grant **only** the permissions a task needs, on **only** the resources it touches, for **only** as long as needed.

| Too broad | Least privilege |
|---|---|
| `"Action": "s3:*"` | `"Action": ["s3:GetObject"]` |
| `"Resource": "*"` | `"Resource": "arn:aws:s3:::reports-bucket/2026/*"` |
| A permanent admin user | A role assumed just-in-time, with MFA |

In practice: start narrow and widen when something legitimately fails, rather than starting with `*` and promising to tighten later. **IAM Access Analyzer** can generate a policy from what an identity actually used.

## IAM best practices

1. **Lock down the root user** — MFA, no access keys.
2. **Use roles, not access keys**, for applications and pipelines. GitHub Actions can assume a role via **OIDC** with no stored secret at all.
3. **MFA for every human.**
4. **Prefer SSO / IAM Identity Center** over individual IAM users.
5. **Least privilege**, reviewed regularly — remove unused permissions.
6. **Use groups**, not per-user policies.
7. **Rotate** any access keys that must exist, and never commit them (the Gitleaks scan in [session 17](../../../../session-17-devsecops/HW/) exists for exactly this).
8. **Use conditions** — require MFA or a source IP for sensitive actions.
9. **Turn on CloudTrail** so every API call is logged.

## Common use cases

- An EC2 instance reading from one S3 bucket → instance **role** with a scoped `s3:GetObject` policy.
- A CI/CD pipeline deploying infrastructure → **role assumed through OIDC**, no stored keys.
- A read-only auditor → **group** with the `ReadOnlyAccess` managed policy.
- Another AWS account needing access → **cross-account role** with a trust policy.

## How it showed up in this session

The Terraform S3 demo deliberately keeps credentials **out of code**: against the emulator it uses dummy values, and against real AWS the provider reads credentials from the environment, a profile or SSO. Hardcoding keys in `provider.tf` is exactly the leak IAM best practices warn against.

# 02 — EC2: Elastic Compute Cloud (Compute)

**Session 18 homework** · Angel Kumar · 24bcs10011

## What is EC2?

EC2 provides **virtual servers ("instances") on demand**. You choose the operating system image, the CPU/memory size and the network, and AWS runs it on its hardware, billed per second. It is the foundational compute service — containers on ECS/EKS and many managed services run on EC2 underneath.

## AMI — Amazon Machine Image

An AMI is the **template an instance boots from**: the OS, pre-installed software and the root volume's snapshot.

- **AWS-provided** — Amazon Linux, Ubuntu, Windows
- **Marketplace** — vendor images with software preinstalled
- **Custom** — your own, built from a configured instance or with Packer ("golden images")

AMIs are **regional**, and their IDs differ per region — which is why Terraform usually looks them up with a `data "aws_ami"` filter rather than hardcoding an ID.

## Instance types

Named `family + generation + size`, e.g. **`t3.micro`**, **`m7g.large`**:

| Family | Optimised for | Example |
|---|---|---|
| **t** — burstable | Low baseline CPU with credits to burst | `t3.micro` — dev servers, small sites |
| **m** — general purpose | Balanced CPU/memory | `m7i.large` — web/app servers |
| **c** — compute | High CPU | `c7i.xlarge` — batch, encoding |
| **r** — memory | High RAM | `r7i.large` — caches, in-memory DBs |
| **g/p** — accelerated | GPUs | `g5.xlarge` — ML inference |

A trailing **`g`** (e.g. `m7g`) means AWS Graviton (ARM) — usually ~20% cheaper for the same work. Relevant here: this whole homework ran on ARM (Apple Silicon), and [session 10](../../../../session10-k8s-core-objects/HW/core-objects/) hit an image that wasn't published for ARM.

## Key pairs

An SSH **public/private key pair**. AWS stores the public key and places it on the instance at launch; you keep the private key (`.pem`) to log in. **AWS never sees or stores your private key** — lose it and you cannot recover SSH access that way.

Modern alternative: **AWS Systems Manager Session Manager** gives shell access through IAM with no SSH keys and no open port 22.

## Security Groups

A **stateful virtual firewall attached to the instance's network interface**.

- Rules are **allow-only** — there's no "deny" rule.
- **Stateful** — if inbound traffic is allowed, the response is automatically allowed back out.
- Can reference **other security groups** as a source: "allow 5432 only from the app-tier SG", instead of IP ranges.
- Default: **all inbound denied, all outbound allowed**.

| Rule | Source | Purpose |
|---|---|---|
| TCP 443 | `0.0.0.0/0` | Public HTTPS |
| TCP 22 | `203.0.113.10/32` | SSH from one admin IP only — never `0.0.0.0/0` |
| TCP 5432 | `sg-app-tier` | DB reachable only from the app servers |

## EBS — Elastic Block Store

Network-attached **block storage volumes** — the instance's "disks".

- Persist **independently** of the instance (the root volume is deleted on termination by default; extra volumes aren't).
- Live in **one Availability Zone** and attach to instances in that AZ.
- **Snapshots** back them up to S3 incrementally, and can be copied across regions.
- Types: **gp3** (general SSD, the default choice), **io2** (provisioned high IOPS, databases), **st1/sc1** (cheap throughput HDD).

Contrast **instance store** — physically attached, very fast, but **wiped when the instance stops**.

## Public vs private IP

| | Private IP | Public IP | Elastic IP |
|---|---|---|---|
| Assigned from | Subnet CIDR | AWS's public pool | Allocated to your account |
| Reachable from | Inside the VPC | The internet | The internet |
| Survives stop/start | **Yes** | **No — changes** | **Yes** — static until released |
| Cost | Free | Charged per hour | Charged per hour |

A public IP alone doesn't make an instance reachable: it must also be in a subnet whose route table points to an **Internet Gateway**, with a security group that allows the traffic (see [VPC](../04-vpc/)).

## Instance lifecycle

```
            launch
              │
              ▼
          pending ──► running ◄──────── start ───────┐
                        │  │                         │
                reboot  │  └──── stop ──► stopping ──► stopped
                        │                               │
                        └──── terminate ──► shutting-down ──► terminated
```

| State | Billed for compute? | Data on EBS | Public IP |
|---|---|---|---|
| running | Yes | Kept | Kept |
| stopped | **No** (still pay for EBS) | Kept | **Released** |
| terminated | No | Root volume deleted by default | Released |

**Stop ≠ terminate.** Stopping is like shutting a laptop; terminating is throwing it away.

## Common use cases

- Web and application servers behind a load balancer, in an **Auto Scaling Group**
- Self-managed databases where RDS doesn't fit
- Kubernetes worker nodes (EKS node groups are EC2 instances)
- CI/CD build runners, batch jobs, ML training (GPU instances)
- Lift-and-shift migrations of existing servers

Built for real with Terraform in [session 19](../../../../session19-cloud-terraform/HW/).

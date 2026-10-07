# 04 — VPC: Virtual Private Cloud (Networking)

**Session 18 homework** · Angel Kumar · 24bcs10011

## What is a VPC?

A VPC is **your own logically isolated network inside AWS**. You choose its IP address range, split it into subnets, and control exactly how traffic gets in, out and around. Every EC2 instance, RDS database or EKS node lives inside one.

Think of it as the data-centre network — but defined in software, created in seconds, and versioned in Terraform.

## CIDR

A VPC gets an IP range written in **CIDR notation**: `10.0.0.0/16`.

The number after the slash is how many bits are **fixed**; the rest are free for hosts.

| CIDR | Addresses | Typical use |
|---|---|---|
| `10.0.0.0/16` | 65,536 | A whole VPC |
| `10.0.1.0/24` | 256 | One subnet |
| `10.0.1.0/28` | 16 | A tiny subnet |

Use **private ranges** (RFC 1918: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) and **plan so VPCs don't overlap** — overlapping ranges cannot be peered or connected later.

AWS reserves **5 addresses in every subnet** (network, router, DNS, future use, broadcast), so a `/24` gives 251 usable IPs.

## Subnets

A subnet is a slice of the VPC's range **in exactly one Availability Zone**.

```
VPC 10.0.0.0/16
├── public-a   10.0.1.0/24   ap-south-1a
├── public-b   10.0.2.0/24   ap-south-1b
├── private-a  10.0.11.0/24  ap-south-1a
└── private-b  10.0.12.0/24  ap-south-1b
```

Spreading subnets across AZs is what makes an architecture survive the loss of one data centre.

## Route tables

Each subnet is associated with a **route table** — the rules for where packets go.

```
Destination    Target
10.0.0.0/16    local          <- every VPC has this: subnets can always reach each other
0.0.0.0/0      igw-0abc...    <- "everything else goes to the internet"
```

**The route table is what makes a subnet public or private.** Nothing else.

## Internet Gateway (IGW)

A horizontally-scaled, highly-available gateway that connects the VPC to the internet. **One per VPC.** It allows both directions — inbound connections to resources with public IPs, and outbound from them.

A subnet is **public** when its route table sends `0.0.0.0/0` to an IGW.

## NAT Gateway

Lets resources in **private** subnets make **outbound** connections (downloading updates, calling APIs) **without** being reachable from the internet.

```
private instance ──► NAT Gateway (in a PUBLIC subnet) ──► Internet Gateway ──► internet
                          ▲
                   inbound connections from the internet: blocked
```

Cost note: NAT Gateways are billed **per hour and per GB processed** — often a surprising line on the bill. Use one per AZ for resilience in production.

## Security Groups vs Network ACLs

| | Security Group | Network ACL |
|---|---|---|
| Attached to | Network interface (instance) | **Subnet** |
| State | **Stateful** — replies automatically allowed | **Stateless** — return traffic needs its own rule |
| Rules | **Allow only** | Allow **and deny** |
| Evaluation | All rules evaluated together | Numbered, **first match wins** |
| Typical role | Primary, fine-grained control | Coarse subnet-wide guardrail, e.g. block a known-bad IP range |

The stateless point catches people out: an NACL allowing inbound 443 must *also* allow outbound **ephemeral ports (1024–65535)** or the responses are dropped.

Security groups were the Kubernetes NetworkPolicy equivalent seen in [session 14](../../../../session-14-kubernetes-troubleshooting/HW/10-pod-networking/) — and like there, the failure mode is "everything looks healthy but packets don't arrive".

## Public vs private subnet

| | Public subnet | Private subnet |
|---|---|---|
| Route `0.0.0.0/0` → | **Internet Gateway** | **NAT Gateway** (or nothing) |
| Reachable from internet | Yes, with a public IP + SG rule | **No** |
| Outbound internet | Directly | Via NAT |
| Put here | Load balancers, bastion hosts, NAT gateways | App servers, databases, internal services |

**The standard layout:** internet-facing load balancer in public subnets, application servers and databases in private subnets — so the only thing exposed to the internet is the load balancer.

```
Internet
   │
[ IGW ]
   │
public subnets:   [ ALB ]   [ NAT GW ]
                     │          ▲
private subnets:  [ App ] ──────┘  (outbound only)
                     │
                  [ RDS ]
```

## Common use cases

- Isolating environments — separate VPCs for dev, staging and prod
- Three-tier apps — web in public subnets, app and DB in private ones
- Hybrid cloud — VPN or Direct Connect into an on-premises network
- Connecting VPCs — peering or Transit Gateway

Built for real with Terraform — VPC, subnet, route table, internet gateway and security group — in [session 19](../../../../session19-cloud-terraform/HW/).

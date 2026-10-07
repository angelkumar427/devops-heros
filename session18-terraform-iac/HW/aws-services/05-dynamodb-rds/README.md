# 05 — DynamoDB & RDS (Database Services)

**Session 18 homework** · Angel Kumar · 24bcs10011

Two managed databases built on opposite ideas: **DynamoDB** is a NoSQL key-value store that scales without limit; **RDS** runs a traditional relational database engine for you.

---

# DynamoDB

## NoSQL

DynamoDB is a **fully managed, serverless NoSQL key-value and document database**. No servers, no patching, no capacity to plan (in on-demand mode), and single-digit-millisecond responses at any scale.

"NoSQL" here means: **no fixed schema, no joins, and access only through the keys you design.** That's the trade — enormous scale and predictable speed, in exchange for designing the table around the queries you'll run.

## Tables, items, attributes

| DynamoDB | Rough relational equivalent |
|---|---|
| **Table** | Table |
| **Item** | Row (max 400 KB) |
| **Attribute** | Column — but each item can have *different* attributes |

```json
{ "OrderId": "ORD-1001", "CustomerId": "C-42", "Total": 1499, "Status": "SHIPPED" }
{ "OrderId": "ORD-1002", "CustomerId": "C-17", "Total": 230, "GiftWrap": true }
```

Both items live in the same table; only the **key attributes** are mandatory.

## Partition key

The **required** primary key component. DynamoDB **hashes** it to decide which physical partition stores the item.

- A table with *only* a partition key: every value must be unique.
- **Choose a high-cardinality key** (`UserId`, `OrderId`). A low-cardinality key like `Status` sends most traffic to a few partitions — a "hot partition" that throttles even when the table as a whole has spare capacity.

## Sort key

An **optional** second key component. Items sharing a partition key are stored **together, ordered by sort key** — which enables range queries.

```
Partition key: CustomerId   Sort key: OrderDate
C-42                        2026-09-01
C-42                        2026-09-15
C-42                        2026-10-07
```

`Query CustomerId = "C-42" AND OrderDate BETWEEN "2026-09-01" AND "2026-09-30"` returns that customer's September orders, already sorted, in one efficient call. Partition key + sort key together must be unique.

**Query vs Scan:** a `Query` uses the key and reads only matching items. A `Scan` reads the entire table — slow and expensive at scale. Design keys so you never need to scan.

**Secondary indexes** (GSI/LSI) add alternative keys for other access patterns.

## Use cases

- Session stores, shopping carts, user profiles
- Gaming leaderboards and player state
- IoT and event data at very high write rates
- Serverless back ends (paired with Lambda)
- **Terraform state locking** — a small DynamoDB table guarantees only one `terraform apply` runs against an S3-backed state at a time

---

# RDS

## Relational database

RDS (Relational Database Service) runs a **standard SQL database engine** while AWS handles the operational work: provisioning, OS and engine patching, backups, failover and monitoring. You still get full SQL — joins, transactions, foreign keys, constraints.

## Supported engines

| Engine | Notes |
|---|---|
| **PostgreSQL** | Open source, rich features |
| **MySQL** | Open source, very widely used |
| **MariaDB** | MySQL-compatible fork |
| **Oracle** | Commercial, bring-your-own-licence or licence-included |
| **SQL Server** | Microsoft, several editions |
| **Db2** | IBM |
| **Aurora** (MySQL / PostgreSQL compatible) | AWS-built, distributed storage, up to ~5x MySQL throughput |

## DB instances

A **DB instance** is the managed server running the engine. You choose:

- an **instance class** (`db.t4g.micro`, `db.r7g.large` — same family logic as [EC2](../02-ec2/))
- **storage** type and size (gp3, io2), with optional autoscaling
- the **VPC subnet group** it lives in — always **private subnets**

## Security

- **Network:** private subnets and a security group allowing the DB port **only from the application tier's security group** ([VPC](../04-vpc/)). Never `0.0.0.0/0`.
- **Encryption at rest** with KMS (must be chosen at creation; covers storage, snapshots and replicas).
- **Encryption in transit** with TLS, enforceable by parameter.
- **Credentials** in **Secrets Manager** with automatic rotation — not in application config files.
- **IAM database authentication** as an alternative to passwords.

## Backups

| Type | How | Retention |
|---|---|---|
| **Automated backups** | Daily snapshot + continuous transaction logs | 1–35 days |
| **Point-in-time recovery** | Restore to any second within the retention window | Within the window |
| **Manual snapshots** | Taken on demand | Kept until you delete them |

A restore creates a **new** instance — it never overwrites the existing one.

## Multi-AZ

A **synchronous standby copy in a second Availability Zone**.

```
   Primary (AZ-a)  ══ synchronous replication ══►  Standby (AZ-b)
        │                                              │
        └── on failure: DNS endpoint flips to standby, typically 60–120s
```

- Purpose: **high availability**, not performance — the standby serves no traffic.
- Failover is automatic, and the connection endpoint stays the same.

## Read replicas

**Asynchronous** copies that **serve read traffic**.

| | Multi-AZ standby | Read replica |
|---|---|---|
| Purpose | Availability | **Read scaling** |
| Replication | Synchronous | Asynchronous (slight lag) |
| Serves traffic | No | **Yes, reads** |
| Can be cross-region | No | **Yes** |
| Can be promoted | Automatic on failure | Manually, to a standalone DB |

Use replicas for reporting queries and read-heavy workloads; use Multi-AZ so an AZ outage doesn't take the database down. Production systems often use both.

## Use cases

- Transactional applications — e-commerce orders, banking, bookings
- Anything needing **joins, transactions and referential integrity**
- CMS platforms and ERP/CRM systems
- Migrating an existing on-premises SQL database to the cloud

---

## Choosing between them

| Question | DynamoDB | RDS |
|---|---|---|
| Data shape | Simple, key-based access | Relational, with joins |
| Query flexibility | Fixed by key design | Any SQL query |
| Scale | Effectively unlimited, automatic | Vertical, plus read replicas |
| Transactions | Supported, limited | Full ACID |
| Operations | Serverless | Managed, but you size the instance |
| Billing | Per request or provisioned capacity | Per instance-hour + storage |

**Rule of thumb:** if you know your access patterns up front and need massive scale, DynamoDB. If you need flexible queries and relational integrity, RDS.

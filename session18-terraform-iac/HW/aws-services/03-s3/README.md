# 03 — S3: Simple Storage Service (Storage)

**Session 18 homework** · Angel Kumar · 24bcs10011

## What is S3?

S3 is **object storage**: you store files ("objects") of any size in containers ("buckets") and fetch them over HTTPS by key. It's designed for **99.999999999% (11 nines) durability** by storing data redundantly across multiple Availability Zones, and it scales without any capacity planning.

It is *not* a filesystem and not a block device — there are no directories to `cd` into and no in-place edits. You `PUT` a whole object and `GET` it back.

## Buckets

- A top-level container for objects, created in **one region**.
- Names are **globally unique across all AWS accounts** — which is why the Terraform demo appends a random suffix (`devops-heros-dev-da5a3515`).
- Bucket-level settings: versioning, encryption, lifecycle rules, public access block, policies, logging.

## Objects

An object = **key** + **data** + **metadata**.

- The **key** is the full name, e.g. `logs/2026/10/07/app.log`. The `/` makes it *look* like folders, but the namespace is flat — "folders" are just a shared key prefix.
- Up to **5 TB** per object (multipart upload above ~100 MB).
- Strong read-after-write consistency.

## Storage classes

| Class | For | Retrieval |
|---|---|---|
| **Standard** | Frequently accessed data | Immediate |
| **Intelligent-Tiering** | Unknown or changing access patterns — moves data automatically | Immediate |
| **Standard-IA** | Infrequent access, still needs fast retrieval | Immediate, retrieval fee |
| **One Zone-IA** | Re-creatable infrequent data, single AZ | Immediate, cheaper, less resilient |
| **Glacier Instant Retrieval** | Archives accessed ~quarterly | Milliseconds |
| **Glacier Flexible Retrieval** | Archives | Minutes to hours |
| **Glacier Deep Archive** | Long-term retention, compliance | Up to ~12 hours, cheapest |

The trade is always **storage price vs. retrieval cost and speed**.

## Versioning

With versioning on, **every overwrite and every delete keeps the previous version**. A delete just adds a *delete marker*; the data is still there and recoverable.

This was observed directly in [the Terraform demo](../../terraform-s3-demo/):

```
version       welcome.txt 7dda6289  latest
version       welcome.txt 26976599
delete-marker welcome.txt c6521a8b
```

One deleted file had become *three* versioned entries — and that's precisely why the bucket couldn't be deleted (`BucketNotEmpty`) until every version was purged. Versioning protects against mistakes and ransomware, at the cost of storing every version and making cleanup deliberate.

Versioning can be **enabled** or **suspended**, but never turned fully off again once enabled.

## Lifecycle policies

Rules that act on objects automatically by age or prefix:

```hcl
rule {
  id     = "archive-then-expire-logs"
  status = "Enabled"
  filter { prefix = "logs/" }

  transition {
    days          = 30
    storage_class = "STANDARD_IA"
  }
  transition {
    days          = 90
    storage_class = "GLACIER"
  }
  expiration { days = 365 }
  noncurrent_version_expiration { noncurrent_days = 30 }   # clean up old versions
}
```

The last line matters with versioning: without it, old versions accumulate (and cost money) forever.

## Encryption

| Option | Keys managed by | Notes |
|---|---|---|
| **SSE-S3** (`AES256`) | AWS | Default for all new buckets; used in the demo |
| **SSE-KMS** | AWS KMS, your key | Key-usage audit trail in CloudTrail, separate key permissions |
| **SSE-C** | You, sent with each request | AWS never stores the key |
| **Client-side** | You, before upload | Data is encrypted before it ever reaches AWS |

**In transit:** HTTPS. Enforce it with a bucket policy denying requests where `aws:SecureTransport` is `false`.

## Bucket policies

Resource-based JSON policies attached to the bucket — they say who may access it, from where, and how.

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyInsecureTransport",
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": ["arn:aws:s3:::my-bucket", "arn:aws:s3:::my-bucket/*"],
    "Condition": { "Bool": { "aws:SecureTransport": "false" } }
  }]
}
```

**Block Public Access** sits above bucket policies and overrides them. All four settings were enabled in the demo and verified via the API:

```
{'BlockPublicAcls': True, 'IgnorePublicAcls': True, 'BlockPublicPolicy': True, 'RestrictPublicBuckets': True}
```

Accidentally public buckets have caused some of the largest data leaks on record; this one setting prevents them.

## Common use cases

- Static website hosting (often behind CloudFront)
- Backups, archives and disaster-recovery copies
- Data lakes for analytics (Athena, EMR, Redshift Spectrum)
- Application file storage — user uploads, images, documents
- **Terraform remote state** — an S3 backend (with a DynamoDB lock table, see [DynamoDB](../05-dynamodb-rds/)) so a team shares one state file safely
- Build artifacts and container image layers

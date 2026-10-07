# Session 18 — Terraform & Infrastructure as Code

**Homework submission** · Angel Kumar · 24bcs10011

> **Terraform:** `v1.16.5` · **AWS provider:** `v5.100.0` · **Target:** Moto, an open-source AWS
> emulator exposing the real AWS APIs locally. Every Terraform command ran for real.

```
HW/
├── terraform-s3-demo/          Task 1 - create an S3 bucket with Terraform
│   ├── main.tf  variables.tf  outputs.tf  provider.tf  terraform.tfvars
│   └── README.md
└── aws-services/               Task 2 - AWS services research
    ├── 01-iam/README.md
    ├── 02-ec2/README.md
    ├── 03-s3/README.md
    ├── 04-vpc/README.md
    └── 05-dynamodb-rds/README.md
```

## Task 1 — Terraform S3 Demo → [`terraform-s3-demo/`](./terraform-s3-demo/)

All eight commands, run in order against a live AWS-compatible API:

| Command | Result |
|---|---|
| `terraform init` | Providers `aws v5.100.0` + `random v3.9.1` installed |
| `terraform fmt` | Already canonically formatted |
| `terraform validate` | `Success! The configuration is valid.` |
| `terraform plan` | `6 to add, 0 to change, 0 to destroy` |
| `terraform apply` | `Resources: 6 added` |
| `terraform show` | Versioned, AES-256 encrypted, public access fully blocked |
| `terraform output` | Bucket name, ARN, region, versioning status, object URI |
| `terraform destroy` | `Resources: 6 destroyed` — bucket confirmed gone from S3 |

![Full workflow](./terraform-s3-demo/screenshots/01-full-workflow.png)

**Also demonstrated:** drift detection — an object deleted by hand was detected by the next `plan` and restored by `apply`.

**Two real problems found and fixed:**
1. **`BucketNotEmpty` on destroy** — versioning keeps every version and delete marker, so the bucket was never empty. Fixed with `force_destroy`, **deliberately disabled for `prod`**.
2. **A missing `depends_on`** between the object and the versioning configuration, which HashiCorp's docs recommend. With it, teardown runs in the correct order and completes in 0 seconds.

| Drift detection | BucketNotEmpty diagnosis |
|---|---|
| ![drift](./terraform-s3-demo/screenshots/02-drift-detection.png) | ![bne](./terraform-s3-demo/screenshots/03-bucket-not-empty.png) |

## Task 2 — AWS Services Research → [`aws-services/`](./aws-services/)

| Service | Category | Covers |
|---|---|---|
| [**01 — IAM**](./aws-services/01-iam/) | Governance | Users, groups, roles, policies, permission evaluation, least privilege, best practices, use cases |
| [**02 — EC2**](./aws-services/02-ec2/) | Compute | AMIs, instance types, key pairs, security groups, EBS, public vs private IP, lifecycle, use cases |
| [**03 — S3**](./aws-services/03-s3/) | Storage | Buckets, objects, storage classes, versioning, lifecycle, encryption, bucket policies, use cases |
| [**04 — VPC**](./aws-services/04-vpc/) | Networking | CIDR, subnets, route tables, IGW, NAT, security groups vs NACLs, public vs private subnets |
| [**05 — DynamoDB & RDS**](./aws-services/05-dynamodb-rds/) | Database | NoSQL tables/items/keys; RDS engines, security, backups, Multi-AZ, read replicas — and when to pick which |

The write-ups connect back to things actually observed in this homework: S3 versioning is illustrated with the real version and delete-marker listing from the demo, and EC2's Graviton note ties to the ARM image issue hit in session 10.

## Key ideas

- **Declarative:** describe the end state; Terraform works out the steps.
- **Plan before apply:** every change is previewed, and saving the plan guarantees what's applied is what was reviewed.
- **State** maps code to real resources — and is kept out of git, since it can contain sensitive values.
- **Drift detection** keeps the code as the source of truth.
- **Destroy needs design too** — versioning, `force_destroy` and environment-specific safety all affect teardown.

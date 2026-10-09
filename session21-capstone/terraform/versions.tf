terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.68"
    }
  }
  # Team setups keep state in S3 with locking, e.g.:
  # backend "s3" { bucket = "<state-bucket>"  key = "stockpilot/eks.tfstate"  region = "ap-south-1"  use_lockfile = true }
}

# Credentials come from the environment / ~/.aws (aws configure) - never from these files.
provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project     = "stockpilot"
      Environment = var.environment
      Owner       = var.owner
      ManagedBy   = "terraform"
    }
  }
}

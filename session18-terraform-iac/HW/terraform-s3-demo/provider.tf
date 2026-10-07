terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# The AWS provider is pointed at a LOCAL AWS emulator (Moto) instead of real AWS.
# Every Terraform command runs for real against a real AWS-compatible API; only
# the endpoint differs. To target real AWS, set use_local_emulator = false and
# supply credentials the normal way (environment, profile or SSO) - never in code.
provider "aws" {
  region = var.aws_region

  access_key                  = var.use_local_emulator ? "test" : null # dummy values the emulator accepts
  secret_key                  = var.use_local_emulator ? "test" : null
  skip_credentials_validation = var.use_local_emulator
  skip_metadata_api_check     = var.use_local_emulator
  skip_requesting_account_id  = var.use_local_emulator
  s3_use_path_style           = var.use_local_emulator

  dynamic "endpoints" {
    for_each = var.use_local_emulator ? [1] : []
    content {
      s3  = var.emulator_endpoint
      sts = var.emulator_endpoint
    }
  }

  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "Terraform"
      Owner     = var.owner
    }
  }
}

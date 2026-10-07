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

# Pointed at a local AWS emulator (Moto) that serves the real EC2/VPC/S3/ECR APIs.
# Set use_local_emulator = false to deploy to real AWS; credentials then come
# from the environment, a profile or SSO - never from this file.
provider "aws" {
  region = var.aws_region

  access_key                  = var.use_local_emulator ? "test" : null
  secret_key                  = var.use_local_emulator ? "test" : null
  skip_credentials_validation = var.use_local_emulator
  skip_metadata_api_check     = var.use_local_emulator
  skip_requesting_account_id  = var.use_local_emulator
  s3_use_path_style           = var.use_local_emulator

  dynamic "endpoints" {
    for_each = var.use_local_emulator ? [1] : []
    content {
      ec2 = var.emulator_endpoint
      ecr = var.emulator_endpoint
      s3  = var.emulator_endpoint
      sts = var.emulator_endpoint
    }
  }

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

variable "aws_region" {
  description = "AWS region to create resources in"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name, used in resource names and tags"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "owner" {
  description = "Owner tag applied to every resource"
  type        = string
}

variable "enable_versioning" {
  description = "Keep previous versions of every object"
  type        = bool
  default     = true
}

variable "use_local_emulator" {
  description = "Target a local AWS emulator instead of real AWS"
  type        = bool
  default     = true
}

variable "emulator_endpoint" {
  description = "Endpoint of the local AWS emulator"
  type        = string
  default     = "http://localhost:4566"
}

variable "project_name" {
  description = "Prefix for every resource name"
  type        = string
  default     = "task-tracker"
}

variable "environment" {
  description = "dev | staging | prod"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging or prod."
  }
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.21.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones to spread the subnets across"
  type        = number
  default     = 2
}

variable "admin_cidr" {
  description = "CIDR allowed to reach the Kubernetes API (6443). Never 0.0.0.0/0."
  type        = string
  validation {
    condition     = var.admin_cidr != "0.0.0.0/0"
    error_message = "admin_cidr must not be open to the whole internet."
  }
}

variable "use_local_emulator" {
  description = "true = talk to the local AWS emulator instead of real AWS"
  type        = bool
  default     = true
}

variable "emulator_endpoint" {
  type    = string
  default = "http://localhost:4566"
}

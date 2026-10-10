variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  type    = string
  default = "capstone"
}

variable "owner" {
  description = "Tag value identifying who owns (and must destroy) these resources"
  type        = string
}

variable "cluster_name" {
  type    = string
  default = "stockpilot-eks"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version; null = the current AWS default"
  type        = string
  default     = null
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "az_count" {
  description = "Availability zones to spread subnets across (EKS needs at least 2)"
  type        = number
  default     = 2
  validation {
    condition     = var.az_count >= 2
    error_message = "EKS requires subnets in at least two availability zones."
  }
}

variable "node_instance_types" {
  type    = list(string)
  default = ["t3.medium"]
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_min_size" {
  type    = number
  default = 1
}

variable "node_max_size" {
  type    = number
  default = 3
}

variable "api_allowed_cidrs" {
  description = "CIDRs allowed to reach the public Kubernetes API endpoint - narrow this to your own IP"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "enable_nat_gateway" {
  description = <<-EOT
    true  = worker nodes in the private subnets, outbound via a NAT gateway (production layout).
    false = no NAT gateway: worker nodes run in the public subnets with auto-assigned public IPs.
            Use when the account has no Elastic IP left (default quota: 5 per region) or to save
            the NAT gateway's hourly cost. Node security groups still admit only cluster traffic.
  EOT
  type        = bool
  default     = true
}

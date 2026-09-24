variable "cluster_name" {
  description = "EKS cluster name."
  type        = string
}

variable "environment" {
  description = "Environment name."
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for EKS."
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_ids) == 2
    error_message = "EKS requires private subnets in two availability zones."
  }
}

variable "instance_types" {
  description = "EKS worker node instance types."
  type        = list(string)
}

variable "desired_nodes" {
  description = "Desired worker node count."
  type        = number
}

variable "min_nodes" {
  description = "Minimum worker node count."
  type        = number
}

variable "max_nodes" {
  description = "Maximum worker node count."
  type        = number
}

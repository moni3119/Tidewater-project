variable "name" {
  description = "Name prefix for Redis resources."
  type        = string
}

variable "environment" {
  description = "Environment name."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for Redis."
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "Redis must use private subnets across at least two availability zones."
  }
}

variable "security_group_ids" {
  description = "Security groups attached to Redis."
  type        = list(string)
}

variable "engine_version" {
  description = "Redis engine version."
  type        = string
  default     = "7.1"
}

variable "node_type" {
  description = "ElastiCache node type."
  type        = string
  default     = "cache.t3.micro"
}

variable "num_cache_clusters" {
  description = "Number of Redis cache nodes."
  type        = number
  default     = 1
}

variable "automatic_failover_enabled" {
  description = "Enable automatic failover."
  type        = bool
  default     = false
}

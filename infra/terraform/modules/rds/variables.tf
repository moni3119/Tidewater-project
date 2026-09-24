variable "name" {
  description = "Name prefix for RDS resources."
  type        = string
}

variable "environment" {
  description = "Environment name."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for RDS."
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "RDS must use private subnets across at least two availability zones."
  }
}

variable "security_group_ids" {
  description = "Security groups attached to RDS."
  type        = list(string)
}

variable "engine_version" {
  description = "PostgreSQL engine version."
  type        = string
  default     = "15"
}

variable "instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Initial storage in GB."
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum storage in GB."
  type        = number
  default     = 50
}

variable "database_name" {
  description = "Application database name."
  type        = string
  default     = "settle"
}

variable "database_username" {
  description = "Database username."
  type        = string
  sensitive   = true
}

variable "database_password" {
  description = "Database password."
  type        = string
  sensitive   = true
}

variable "multi_az" {
  description = "Enable Multi-AZ deployment."
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "Number of days to retain automated backups."
  type        = number
  default     = 7
}

variable "deletion_protection" {
  description = "Prevent accidental database deletion."
  type        = bool
  default     = false
}

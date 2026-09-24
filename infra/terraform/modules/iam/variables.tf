variable "name" {
  description = "Name prefix for IAM resources."
  type        = string
}

variable "environment" {
  description = "Environment name."
  type        = string
}

variable "secret_arn" {
  description = "ARN of the application secret."
  type        = string
}

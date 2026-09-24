provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Tidewater"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

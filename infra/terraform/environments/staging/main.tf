module "vpc" {
  source = "../../modules/vpc"

  name        = "tidewater-${var.environment}"
  environment = var.environment

  vpc_cidr = "10.20.0.0/16"

  availability_zones = [
    "ap-south-1a",
    "ap-south-1b"
  ]

  public_subnet_cidrs = [
    "10.20.1.0/24",
    "10.20.2.0/24"
  ]

  private_subnet_cidrs = [
    "10.20.11.0/24",
    "10.20.12.0/24"
  ]
}

# --------------------------------------------------
# EKS Security Group
# --------------------------------------------------

resource "aws_security_group" "eks" {
  name        = "tidewater-${var.environment}-eks"
  description = "Security group for Tidewater EKS workloads"
  vpc_id      = module.vpc.vpc_id
}


# --------------------------------------------------
# RDS Security Group
# --------------------------------------------------

resource "aws_security_group" "rds" {
  name        = "tidewater-${var.environment}-rds"
  description = "PostgreSQL access from EKS"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "PostgreSQL from EKS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks.id]
  }
}

# --------------------------------------------------
# Redis Security Group
# --------------------------------------------------

resource "aws_security_group" "redis" {
  name        = "tidewater-${var.environment}-redis"
  description = "Redis access from EKS"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "Redis from EKS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks.id]
  }
}

# --------------------------------------------------
# EKS
# --------------------------------------------------

module "eks" {
  source = "../../modules/eks"

  cluster_name       = "tidewater-${var.environment}"
  environment        = var.environment
  kubernetes_version = "1.34"

  private_subnet_ids = module.vpc.private_subnet_ids

  instance_types = [
    "t3.small"
  ]

  desired_nodes = 1
  min_nodes     = 1
  max_nodes     = 3
}

# --------------------------------------------------
# RDS PostgreSQL
# --------------------------------------------------

module "rds" {
  source = "../../modules/rds"

  name        = "tidewater-${var.environment}"
  environment = var.environment

  private_subnet_ids = module.vpc.private_subnet_ids

  security_group_ids = [
    aws_security_group.rds.id
  ]

  database_username = var.db_username
  database_password = var.db_password

  instance_class = "db.t3.micro"
  multi_az       = false
}

# --------------------------------------------------
# Redis
# --------------------------------------------------

module "redis" {
  source = "../../modules/redis"

  name        = "tidewater-${var.environment}"
  environment = var.environment

  private_subnet_ids = module.vpc.private_subnet_ids

  security_group_ids = [
    aws_security_group.redis.id
  ]

  node_type                  = "cache.t3.micro"
  num_cache_clusters         = 1
  automatic_failover_enabled = false
}

# --------------------------------------------------
# IAM Workload Role
# --------------------------------------------------

module "iam" {
  source = "../../modules/iam"

  name        = "tidewater-${var.environment}"
  environment = var.environment

  secret_arn = "arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:tidewater/${var.environment}/database"
}

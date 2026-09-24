resource "aws_db_subnet_group" "this" {
  name       = "${var.name}-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.name}-subnet-group"
    Environment = var.environment
  }
}

resource "aws_kms_key" "rds_performance_insights" {
  description         = "KMS key for RDS Performance Insights"
  enable_key_rotation = true

  tags = {
    Name        = "${var.name}-rds-performance-insights"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "rds_performance_insights" {
  name          = "alias/${var.name}-rds-performance-insights"
  target_key_id = aws_kms_key.rds_performance_insights.key_id
}

resource "aws_db_instance" "this" {
  identifier = "${var.name}-postgres"

  engine         = "postgres"
  engine_version = var.engine_version

  instance_class        = var.instance_class
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage

  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.database_name
  username = var.database_username
  password = var.database_password
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = var.security_group_ids

  publicly_accessible = false

  multi_az = var.multi_az

  # Security and monitoring
  performance_insights_enabled        = true
  performance_insights_kms_key_id     = aws_kms_key.rds_performance_insights.arn
  iam_database_authentication_enabled = true
  deletion_protection                 = true

  backup_retention_period = 7

  skip_final_snapshot = true

  tags = {
    Name        = "${var.name}-postgres"
    Environment = var.environment
  }
}

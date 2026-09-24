# Terraform Infrastructure Review

## Scope

The original AWS Terraform draft was reviewed and restructured into
reusable modules for the Tidewater staging and production environments.

The infrastructure has not been applied to a real AWS account.

## Findings and Fixes

### 1. No clear environment separation

**Impact:** Staging and production could become difficult to manage
without duplicated configuration.

**Fix:** Created reusable Terraform modules with separate staging and
production environment configurations.

### 2. Network design needed explicit multi-AZ separation

**Impact:** A single availability zone would create a larger failure
domain.

**Fix:** VPC module defines two availability zones with public and
private subnets.

### 3. Database and Redis should remain private

**Impact:** Publicly accessible data services increase attack surface.

**Fix:** RDS and Redis are placed in private subnets and use dedicated
security groups.

### 4. Database access was not sufficiently isolated

**Impact:** Broad network access could allow unintended clients to
connect to PostgreSQL.

**Fix:** PostgreSQL security group permits TCP/5432 only from the EKS
cluster security group.

### 5. Redis access was not sufficiently isolated

**Impact:** Broad Redis access could expose application queue/cache
data.

**Fix:** Redis security group permits TCP/6379 only from the EKS
cluster security group.

### 6. Terraform state needs centralized storage and locking

**Impact:** Local state can be lost, shared incorrectly or modified
concurrently.

**Fix:** S3 remote state with encryption and DynamoDB locking is
defined for staging and production.

The backend resources themselves are not created by this assignment;
no real AWS apply was performed.

### 7. Application secrets must not be stored in source control

**Impact:** Credentials committed to Git can become permanently
exposed through repository history.

**Fix:** Environment-specific `terraform.tfvars` files are excluded
from Git. Example files contain only placeholders. The design uses
AWS Secrets Manager and IAM-based workload access.

### 8. Compute platform

**Impact:** The AWS target needs a managed Kubernetes path that aligns
with the existing Kubernetes deployment model.

**Fix:** EKS was selected and documented in `docs/DECISIONS.md`.

### 9. Network observability

**Impact:** VPC traffic without flow logging reduces visibility during
security and troubleshooting investigations.

**Fix:** VPC Flow Logs are configured to CloudWatch Logs with a
customer-managed KMS key and 30-day retention.

### 10. Encryption and security hardening

**Impact:** Sensitive infrastructure data and service telemetry should
use controlled encryption and security settings.

**Fixes include:**

- EKS secrets encrypted with customer-managed KMS.
- EKS control-plane logs enabled.
- EKS API endpoint configured for private access.
- RDS storage encryption enabled.
- RDS Performance Insights uses customer-managed KMS encryption.
- Redis encryption at rest and in transit enabled.
- VPC Flow Logs use customer-managed KMS encryption.

## Validation

The final Terraform configuration was checked with:

- `terraform fmt -check -recursive infra\terraform`
- `terraform validate` — staging
- `terraform validate` — production
- `tflint` — clean
- `trivy config infra\terraform` — 0 misconfigurations

No real AWS deployment will be performed for this assignment.
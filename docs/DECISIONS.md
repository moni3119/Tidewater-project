# Architecture Decision Records

## ADR-001: Kubernetes compute platform

### Context
The current Tidewater service runs on a local Kubernetes cluster.
The AWS target design needs a managed compute platform.

### Options
- Amazon EKS
- Amazon ECS on Fargate

### Decision
Use Amazon EKS for the target AWS design.

### Consequences
EKS keeps the Kubernetes deployment model consistent between the
local environment and AWS. Kubernetes manifests and operational
knowledge can be reused.

The trade-off is additional AWS control-plane and cluster-management
complexity compared with ECS Fargate.

---

## ADR-002: Expand-only database migrations

### Context
Migration 0008 previously created a compatibility problem during
rolling deployments and made application rollback unsafe.

### Options
- Destructive migration with a down migration
- Expand/contract migration

### Decision
Use an expand-only migration strategy.

Migration 0008 only adds the nullable `processing_version` column
and its index. Existing columns are not removed or modified.

### Consequences
Old and new application versions can run against the expanded schema.
Application rollback does not require a database down migration.

---

## ADR-003: Bounded PostgreSQL connection pooling

### Context
PostgreSQL has a maximum connection limit of 100 and the API can
scale through an HPA.

### Decision
Use a PostgreSQL connection pool with a maximum of 5 connections
per API pod.

The HPA maximum is 10 API pods.

Maximum API pool usage:

10 pods × 5 connections = 50 connections

This leaves connection capacity for workers, migrations,
monitoring and PostgreSQL itself.

### Consequences
The application cannot create an unbounded number of PostgreSQL
connections during scaling or traffic spikes.
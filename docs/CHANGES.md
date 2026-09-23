# Tidewater Changes

## Task A — Incident investigation

- Added `docs/RCA.md`.
- Documented the incident timeline and causal chain using the
  available evidence.
- Documented findings that could not be independently reproduced.
- Added corrective actions with priorities and role-based owners.

## Task B — Runtime hardening

### Health checks

Separated liveness and readiness responsibilities.

- `/healthz` checks that the API process is alive.
- `/readyz` checks PostgreSQL availability.

This prevents a slow PostgreSQL dependency from directly causing
container restarts.

### Database connection pooling

Added a bounded PostgreSQL connection pool.

The API pool is limited to 5 connections per pod.

With a maximum of 10 API replicas:

10 × 5 = 50 maximum API connections.

This keeps API connection usage below PostgreSQL's 100 connection
limit and leaves capacity for other workloads and maintenance.

### Kubernetes resources

Added CPU and memory requests and limits to the API and worker
deployments.

### Worker reliability

Added recovery of pending Redis stream messages using `XAUTOCLAIM`
and bounded retry behaviour.

This reduces the risk of leaving in-flight work permanently pending
after worker interruption.

### Container security

The API and worker containers run as non-root UID 10001.

### Secrets

Removed the database password from tracked Kubernetes configuration.

The repository contains a placeholder Secret manifest and the local
secret value is kept in the ignored `secret.local.yaml`.

### Nginx

Added explicit upstream and proxy timeout configuration.

This prevents the proxy from using an unbounded or unsuitable timeout
configuration.

---

## Task C — Safe delivery

### Testing

Added API tests for:

- `/healthz`
- `/`

The tests run inside the application container.

### Immutable image

The pipeline builds the API image once using the Git commit SHA as
the immutable image reference.

The same image artifact is then used by later pipeline stages.

### Image scanning

Added a Trivy image scanning stage that checks for HIGH and CRITICAL
vulnerabilities.

### Deployment verification

Added Kubernetes rollout verification and health/readiness checks.

### Automatic rollback

A failed deployment verification triggers an automatic rollback to
the previous known-good application version.

### Migration safety

Redesigned migration 0008 as an expand-only migration.

It adds the nullable `processing_version` column and an index without
removing or changing existing schema elements.

This allows application versions to run side-by-side and avoids the
need for a database down migration during application rollback.

### Faulty release demonstration

Added `Dockerfile.1.9.1-rc` as a reproducible faulty release fixture.

The recording demonstrates:

1. Successful 1.9.0 deployment.
2. Deployment of 1.9.1-rc.
3. Failed rollout verification.
4. Automatic rollback.
5. Alert notification.
6. Recovery to 1.9.0.

---

## Local developer workflow

Added a Makefile with:

- `make up`
- `make down`
- `make status`
- `make test`

Added `scripts/record-demo.ps1` to reproduce the Task C deployment
and automatic rollback demonstration.
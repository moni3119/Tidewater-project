# AI Usage

AI assistance was used during the development of Project Tidewater.

## Areas where AI assistance was used

### 1. Incident investigation

AI was used to help structure the RCA and organize the observed
failure modes, including health-probe failures, database connection
limits and duplicate-payment scenarios.

All conclusions were checked against the available project evidence
and local reproduction results.

### 2. Kubernetes configuration

AI assistance was used to review and improve Kubernetes manifests,
including:

- Liveness and readiness probes
- Resource requests and limits
- Horizontal Pod Autoscaler configuration
- Secret references
- Worker deployment configuration

### 3. Database migration strategy

AI was used to help design the backward-compatible expand-only
migration approach.

Migration `0008` was implemented as an additive schema change so
that old and new application versions can run simultaneously.

### 4. CI/CD pipeline

AI assistance was used to structure the GitHub Actions pipeline and
the local deployment demonstration.

The pipeline includes:

- Tests
- Immutable image build
- Image scanning
- Kubernetes deployment
- Deployment verification
- Automatic rollback on verification failure

### 5. Documentation

AI assistance was used to improve the structure and clarity of:

- `docs/RCA.md`
- `docs/RELEASE.md`
- `docs/DECISIONS.md`
- `docs/RUNBOOK.md`
- `docs/CHANGES.md`
- `docs/NOT-DONE.md`

## Human verification

The implementation was tested locally by running the application,
Kubernetes workloads and deployment demonstration.

The faulty `1.9.1-rc` image was intentionally deployed and the
deployment verification detected the failure and automatically
rolled back to the working `1.9.0` release.

AI-generated suggestions were treated as assistance only. Commands,
configuration and implementation decisions were reviewed and tested
before being included in the project.
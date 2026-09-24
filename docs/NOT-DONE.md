# Not Done

The following items were deliberately left out of the implementation
or kept at design/proof level.

## 1. Historical 14 Aug alert-timing analysis

Priority: High

The original `incident-2026-08-14` evidence bundle was not available
in the working repository or local project.

Therefore, the historical calculation of:
- which Task E alerts would have fired on 14 Aug
- how many minutes earlier they would have fired than the actual detection

could not be independently verified.

No historical alert timing or evidence numbers have been invented.

---

## 2. Real AWS deployment

Priority: High

The Terraform infrastructure was reviewed and designed for AWS, but
it was not applied to a real AWS account.

Reason:

The assignment explicitly requires that the infrastructure not be
applied to a real AWS account.

---

## 3. Production alert notification integration

Priority: Medium

Prometheus alerts are implemented locally, but they are not connected
to a production incident notification system.

A production environment should connect alerts to Slack, PagerDuty or
an equivalent on-call platform.

---

## 4. Image signing and admission verification

Priority: Medium

Container image signing with cosign and admission-time verification
was not implemented.

This would provide stronger supply-chain protection in production.

---

## 5. Default-deny Kubernetes NetworkPolicy

Priority: Medium

A namespace-wide default-deny NetworkPolicy was not implemented.

A production deployment should explicitly allow only the required
API, worker, PostgreSQL, Redis and ingress communication paths.

---

## 6. Chaos testing

Priority: Low

The optional database chaos target was not implemented.

A future improvement would inject PostgreSQL latency and verify that
the API remains available while readiness and retry behaviour operate
as designed.

---

## 7. Production-grade secret management

Priority: High

The local implementation uses a Kubernetes Secret for the demonstration.

A production AWS implementation should use AWS Secrets Manager and
workload identity/IAM-based access.

---

## 8. Full production tracing

Priority: Medium

Structured JSON logging and API-to-worker correlation IDs were
implemented and verified locally.

Full distributed tracing with OpenTelemetry or an equivalent tracing
platform was not implemented.

This should be considered before a production rollout.
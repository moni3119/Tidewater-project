# Not Done

The following items were deliberately left out of the implementation
or kept at design/proof level.

## 1. Real AWS deployment

Priority: High

The Terraform infrastructure was reviewed and designed for AWS, but
it was not applied to a real AWS account.

Reason:

The assignment explicitly requires that the infrastructure not be
applied to a real AWS account.

---

## 2. Full production observability stack

Priority: High

A complete Prometheus and Grafana production monitoring deployment
was not completed as part of the current implementation.

The deployment rollback demonstration instead uses Kubernetes rollout
verification and an explicit deployment-failure alert signal.

A production implementation should provide persistent metrics,
dashboards and alert routing.

---

## 3. Production alert notification integration

Priority: Medium

The local demonstration shows the deployment verification alert
firing in the deployment workflow.

A production environment should connect the alert to an incident
notification system such as Slack, PagerDuty or an equivalent
on-call platform.

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

A production AWS implementation should use a managed secret system
such as AWS Secrets Manager and workload identity/IAM-based access.

---

## 8. Further application observability

Priority: Medium

Structured JSON logging, distributed tracing and full API/worker
correlation were not completed to production depth.

These should be added before a real production rollout.
# Project Tidewater - Incident RCA

## 1. Incident Summary

Date of local reproduction: 23 September 2026

The Tidewater settlement service was deployed locally on a k3d Kubernetes
cluster using the inherited v1.8.0-style configuration.

The reproduction focused on:

- Kubernetes API pod health-check behavior
- PostgreSQL slowdown
- Database-backed API traffic
- HPA behavior
- Pod restarts and readiness/liveness failures
- Worker and settlement processing behavior

The local reproduction confirmed API pod instability caused by aggressive
liveness/readiness probe configuration when the API became slow or temporarily
unavailable.

The assignment scenario also describes intermittent 502/504 responses,
DiskPressure and duplicate payments. Those specific symptoms were not all
reproduced in this local environment, so they are not claimed as locally
verified findings.

---

## 2. Environment

### Application components

- settle-api
- settle-worker
- PostgreSQL 15
- Redis 7
- Mock bank service
- Kubernetes/k3d
- Kubernetes HPA

### API image

`settle-api:1.8.0`

### PostgreSQL configuration

The PostgreSQL instance was verified with:

`max_connections = 100`

Evidence:

- `incident-2026-09-23/postgres-max-connections.txt`

---

## 3. Reproduction Timeline

### Initial v1.8.0 state

The API deployment was running with two replicas.

The API pods showed restart activity before the deliberate database
slowdown test.

Evidence:

- `incident-2026-09-23/pods.txt`
- `incident-2026-09-23/api-pod-describe.txt`

One API pod had multiple restarts and showed the following probe
configuration:

- liveness initial delay: 5 seconds
- liveness period: 5 seconds
- liveness timeout: 1 second
- liveness failure threshold: 1
- readiness timeout: 1 second
- readiness failure threshold: 1

This configuration gives Kubernetes very little tolerance for temporary
application slowness.

### Probe failures

Kubernetes events showed liveness probe failures including connection
refused and timeout/deadline-exceeded errors.

The kubelet subsequently killed/restarted the affected container.

Evidence:

- `incident-2026-09-23/api-pod-describe.txt`
- `incident-2026-09-23/events.txt`
- `incident-2026-09-23/final-events.txt`

### Database slowdown test

A PostgreSQL `pg_sleep()` test was introduced to deliberately make a
database operation slow.

The test was combined with database-backed API requests.

During the reproduction, API pod instability was observed, including
terminating/restarted pods and readiness failures.

Evidence:

- `incident-2026-09-23/final-reproduction-events.txt`
- `incident-2026-09-23/reproduction-events.txt`
- `incident-2026-09-23/real-load-events.txt`
- `incident-2026-09-23/final-events.txt`

### Load test

Database-backed GET requests were sent to the settlement API while the
database slowdown was active.

The API continued serving some requests, but pod instability and probe
failures occurred during the test.

Evidence:

- `incident-2026-09-23/real-load-pods.txt`
- `incident-2026-09-23/real-load-hpa.txt`
- `incident-2026-09-23/real-load-metrics.txt`
- `incident-2026-09-23/final-reproduction-events.txt`

---

## 4. Confirmed Findings

### Finding 1 - Aggressive health probes

The v1.8.0 API used a 1-second timeout and a failure threshold of 1 for
both liveness and readiness probes.

This means a single failed probe could immediately affect container
health status.

Evidence:

- `incident-2026-09-23/api-pod-describe.txt`

### Finding 2 - Liveness failures caused container restarts

Kubernetes recorded liveness failures caused by connection-refused and
deadline-exceeded conditions.

The affected container was killed by the kubelet and restarted.

Evidence:

- `incident-2026-09-23/events.txt`
- `incident-2026-09-23/api-pod-describe.txt`

### Finding 3 - Readiness failures occurred during the slowdown

Readiness probes also failed with timeout/deadline-exceeded conditions.

Readiness failures remove a pod from normal Service endpoints, while
liveness failures can cause the container itself to restart.

Evidence:

- `incident-2026-09-23/final-events.txt`
- `incident-2026-09-23/final-reproduction-events.txt`

### Finding 4 - HPA reacted to increased CPU

The reproduction included HPA scaling activity while load was being
generated.

Evidence:

- `incident-2026-09-23/real-load-hpa.txt`
- `incident-2026-09-23/final-hpa.txt`

HPA scaling alone was not identified as the root cause. It is treated as
a response to workload/resource pressure.

---

## 5. Root Cause

### Primary reproduced failure mode

The primary reproduced failure mode was an overly aggressive Kubernetes
health-check configuration.

The API's liveness probe used:

- 1 second timeout
- 5 second period
- failure threshold of 1

When the API became temporarily slow or unavailable, Kubernetes treated
the failed liveness check as a container failure.

This resulted in:

1. Liveness probe failure
2. Kubelet terminating the container
3. Container restart
4. Temporary loss of the affected API instance
5. Additional readiness/liveness instability while the service recovered

The database slowdown and database-backed load demonstrated a realistic
condition under which this configuration becomes unsafe.

---

## 6. Contributing Factors

The following factors increased the impact:

### 6.1 Liveness probe depended on application responsiveness

The liveness endpoint was served by the same application process that
could become unavailable during resource or database pressure.

A liveness check should determine whether the process is fundamentally
alive, not aggressively restart the application because a dependency is
temporarily slow.

### 6.2 Readiness and liveness were too similar

Both probes used the same very short timeout and failure threshold.

Readiness should normally be used to stop sending traffic to a pod that
cannot safely serve requests.

Liveness should be much more conservative because a failed liveness check
can trigger a restart.

### 6.3 No sufficient failure tolerance

A temporary one-second delay was enough to trigger a probe failure.

The configuration therefore had insufficient tolerance for transient
latency.

### 6.4 Database slowdown increased application latency

The local reproduction deliberately slowed PostgreSQL and generated
database-backed API traffic.

This created the conditions in which the aggressive health probes became
unstable.

The evidence demonstrates correlation between the slowdown test and API
instability, but it does not prove that the database slowdown was the
only cause of every restart.

---

## 7. 502/504 Verification

The assignment scenario describes intermittent 502/504 responses.

The local reproduction did not establish a reliable 502/504 failure.

The initial direct load test through:

`http://localhost:8080/`

was not usable as 502/504 evidence because the nginx/ingress layer had not
yet been configured.

Subsequent API testing was performed through Kubernetes Service
port-forwarding.

Therefore this RCA does **not** claim that 502/504 responses were
reproduced.

A future nginx/ingress test will be required to reproduce and measure
gateway-level 502/504 behavior.

---

## 8. DiskPressure Verification

DiskPressure was not established as a local root cause during this
reproduction.

The assignment scenario mentions node DiskPressure, but the current local
evidence does not prove that DiskPressure caused the observed API restarts.

It will therefore be treated as an assignment-provided incident symptom,
not as a locally verified root cause.

---

## 9. Duplicate Payment Analysis

The settlement service uses an idempotency key for settlement creation.

The local settlement test created a settlement and the worker successfully
processed it.

The local reproduction did not establish 37 duplicate merchant payments.

Therefore the reported 37 duplicate payments from the assignment scenario
are not presented as locally reproduced evidence.

A likely failure mode that must be prevented in the worker is:

1. Worker sends payout to bank.
2. Bank successfully processes payout.
3. Worker fails before recording the successful state locally.
4. Worker retries the same message.
5. The external bank call must be idempotent.

The local mock bank uses the settlement ID as its idempotency key, which
allows repeated requests for the same settlement to be recognized as
already processed.

This behavior will be strengthened and documented as part of the worker
hardening work.

---

## 10. Capacity Analysis

PostgreSQL was verified with:

`max_connections = 100`

The API currently creates a database connection for a database-backed
request.

The Kubernetes HPA is configured with:

- minimum replicas: 2
- maximum replicas: 10

The production scenario describes 4 Uvicorn workers per API pod.

Therefore the theoretical application-side connection demand can become
significant as replicas and workers increase.

The final production design must use bounded connection pooling and
calculate the maximum database connection budget before allowing HPA
scaling.

A safe design must reserve connections for:

- API traffic
- workers
- migrations/admin operations
- monitoring/maintenance
- PostgreSQL internal requirements

The corrected configuration will document the connection budget explicitly.

---

## 11. Evidence Index

| Evidence | Purpose |
|---|---|
| `api-pod-describe.txt` | API pod configuration, probes and restart state |
| `api-previous.log` | Logs from a previously terminated API container |
| `events.txt` | Kubernetes probe/restart events |
| `postgres-max-connections.txt` | PostgreSQL connection limit |
| `db-counts.txt` | Database state during reproduction |
| `hpa.txt` | Initial HPA state |
| `real-load-hpa.txt` | HPA state during load |
| `real-load-pods.txt` | API pod state during load |
| `real-load-metrics.txt` | Resource metrics during load |
| `real-load-events.txt` | Kubernetes events during load |
| `final-reproduction-events.txt` | Events from the final DB-backed reproduction |
| `final-pods.txt` | Final cluster pod state |
| `final-hpa.txt` | Final HPA state |
| `final-metrics.txt` | Final resource metrics |
| `final-events.txt` | Final Kubernetes event history |

---

## 12. Corrective Actions

The following fixes will be implemented in the 1.9.x work:

1. Separate readiness and liveness responsibilities.
2. Increase probe timeout/failure tolerance.
3. Add a dependency-aware readiness check.
4. Prevent slow PostgreSQL from causing cluster-wide restart behavior.
5. Add bounded database connection pooling.
6. Set resource requests and limits based on observed workload.
7. Improve worker retry and acknowledgement behavior.
8. Preserve in-flight jobs during worker restarts.
9. Add structured application logging.
10. Add correlation/request identifiers.
11. Add Prometheus metrics and alerts.
12. Add automated deployment verification.
13. Add automatic rollback for failed releases.
14. Ensure secrets are not stored in images or source control.

---

## 13. RCA Conclusion

The local reproduction demonstrated that the inherited v1.8.0 Kubernetes
configuration was not tolerant of temporary API latency.

The strongest directly observed failure mechanism was the aggressive
liveness/readiness configuration combined with API instability during
database-backed load.

The reproduction does not establish every symptom described in the
assignment scenario. In particular, 502/504 responses, DiskPressure and
the reported duplicate-payment count were not independently reproduced.

Those limitations are intentionally documented so that the RCA distinguishes
verified evidence from scenario information.

The main remediation priority is therefore to make health checks,
database connection handling, worker processing and deployment rollback
safe under transient dependency and resource pressure.
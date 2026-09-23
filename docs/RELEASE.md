# Tidewater Release and Migration Strategy

## Migration 0008

Migration `0008_settlement_metadata_expand.sql` uses an expand-only
migration strategy.

It adds the nullable `processing_version` column to `settlements`
and creates an index for that column.

The migration does not remove or modify existing columns.

## Why this supports rolling deployment

The schema expansion is backward-compatible.

The release sequence is:

1. Deploy migration 0008.
2. Deploy application v1.8 alongside v1.7.
3. Allow v1.7 and v1.8 to run at the same time.
4. Verify v1.8 health and readiness.
5. Route normal traffic to v1.8.
6. Keep v1.7 available during the rollout window.
7. If verification fails, roll back the application deployment to v1.7.
8. Do not run a down migration during rollback.

## Rollback principle

Application rollback and database rollback are separate operations.

A failed application release is rolled back by deploying the previously
known-good application image.

Migration 0008 does not need to be reversed because it only adds a
backward-compatible schema element.

## Release sequence

```text
Migration 0008
      |
      v
v1.7 + v1.8 running together
      |
      v
Health/readiness verification
      |
      +------ success ------> v1.8 remains deployed
      |
      +------ failure ------> deploy v1.7
                                |
                                v
                         verify v1.7
```
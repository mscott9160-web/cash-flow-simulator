# Operations Decision Record

**Decision date:** 2026-09-13
**Decision owner:** MScott
**Applies to:** Stable portfolio release and synthetic Render staging

## Decision

Keep the current Render PostgreSQL staging environment synthetic-only until a paid or otherwise approved Render plan with managed backup retention and point-in-time recovery is selected and verified.

Do not accept real financial data in the current environment.

## Evidence

- A PostgreSQL 18 logical backup was created from the Render staging database.
- The backup restored successfully into a disposable local PostgreSQL 18 target.
- Restored counts matched the rehearsal dataset: 10 users, 8 accounts, 12 items, and 2 overrides.
- Alembic reported revision `20260816_0001 (head)` and `upgrade head` was a no-op.
- The restored application returned `/health` and `/ready` with HTTP 200.
- Render exposed a Free-plan limitation: a second active free database could not be created, and managed recovery capability was not verifiable from the Recovery page.

## Recovery Targets

The local rehearsal demonstrates logical backup and restore, but it does not establish Render-managed recovery guarantees.

Before real-data use, record:

- Backup retention period.
- Point-in-time recovery availability.
- Recovery point objective (RPO).
- Recovery time objective (RTO).
- Backup access owner.
- Restore approval and rollback procedure.

## Consequences

- Portfolio demonstrations and synthetic staging remain approved.
- Internal iOS testing remains approved with fictional data.
- Real financial data and broad public production remain blocked.
- The team can defer paid Render recovery costs until there is a clear need for real-data testing or public production.

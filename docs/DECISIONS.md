# Product And Release Decisions

**Recorded:** 2026-08-24  
**Decision owners:** MScott with Riley, Devon, and Casey review

## Locked Decisions

### Hosting

Use **Render** for staging and the first production deployment:

- Render Web Service for FastAPI
- Render Static Site for the React/Vite website
- Render PostgreSQL for hosted persistence
- Separate staging and production environments
- Separate database and `AUTH_SECRET` per environment

### First Release Audience

The first release is a **portfolio demo for recruiters and managers**, not an unmoderated consumer beta.

The demo should use fictional data, synthetic accounts, and a resettable environment. No real financial information should be entered into the shareable demo.

### Demo And Staging Separation

Maintain two isolated experiences:

- **Portfolio demo:** synthetic data, resettable, clearly labeled as demo data.
- **Staging:** empty or disposable test data for invited technical testers and deployment verification.

They must not share a database, credentials, backups, or account records.

### Product Contract

V1 supports:

- US users
- USD currency
- Cents precision
- US federal holiday calendar
- Saturday/Sunday non-business days
- America/New_York as the initial timezone
- Manual data entry only
- One user-owned cash account
- 90-day default projection horizon
- Hypothetical, advisory bill-date recommendations
- Explicit Apply/Undo scenario changes
- No bank connection, payment execution, or financial advice

### Recommendation Semantics

The optimizer is advisory. It must show the affected bill, original date, proposed date, constraints, and before/after impact. Apply changes the simulator scenario only. It does not contact a biller, move money, or guarantee a bank posting date.

The user-facing launch experience presents one best explainable move. Multi-step optimization may remain an internal engine capability until the UI intentionally supports it.

## Acceptance Criteria For Portfolio Demo

- A reviewer understands the product promise within one minute.
- A reviewer can use synthetic data to find a negative day.
- A reviewer can see which events cause the shortfall.
- A reviewer can inspect one hypothetical bill-date recommendation.
- Apply and Undo clearly change only the simulator scenario.
- Demo data is labeled and resettable.
- No real credentials, financial records, database URLs, or secrets are exposed.
- Web and mobile use the same API behavior.
- CI remains green.

## Release Blockers Before Invited Real-Data Testers

- Publish privacy, terms, support, retention, export, and account deletion behavior.
- Remove unlabeled/stale sample data from authenticated user workspaces.
- Provision hosted PostgreSQL and rehearse Alembic migrations.
- Enable automated backups and test restoration against the hosted database.
- Deploy HTTPS API and web services.
- Add hosted error tracking, logs, uptime checks, and alert ownership.
- Add login abuse protection and rate limiting.
- Complete dependency audit review.
- Test mobile distribution outside the developer LAN, preferably through TestFlight/internal testing.

## Open Infrastructure Inputs

These require owner credentials or account decisions before implementation:

- Render account and service ownership
- Domain name, if a custom URL is desired
- Production and staging database plans
- Secret storage and rotation process
- Error tracking provider
- Uptime monitoring provider
- Apple/Google mobile distribution decision

## Review History

- Business review: Riley approved the focused portfolio-demo scope and deferred consumer-beta complexity.
- Technical review: Devon recommended Render and separate staging/production environments.
- Customer review: Casey required synthetic demo isolation, visible assumptions, and clear hypothetical recommendation language.

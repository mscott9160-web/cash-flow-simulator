# Project Progress

**Project:** Cashflow Simulator  
**Owner:** MScott  
**Repository:** [github.com/mscott9160-web/cash-flow-simulator](https://github.com/mscott9160-web/cash-flow-simulator)  
**Development branch:** `test-com/development`  
**Stable branch:** `master`

## One-Line Summary

A daily cash-flow simulator that identifies negative-balance days and searches for one constrained bill-scheduling change that could improve them.

## Current Status

**Overall:** Core product complete; staging infrastructure prepared
**Last verified:** 2026-08-24
**Latest development commit:** `850b44f`
**Stable portfolio commit:** `e43cf4a`

## Delivery Board

| Phase | Status | Evidence |
| --- | --- | --- |
| 1. Projection engine | Complete | Recurrence, holidays, settlement shifts, decimal balances, 40 backend tests |
| 2. FastAPI and persistence | Complete | Auth, ownership, CRUD, SQLite, Alembic, SQLAlchemy, PostgreSQL URL support |
| 3. Web product workflow | Complete | Login, setup, projection, item CRUD, pause/resume, optimizer, Apply/Undo |
| 4. Mobile product workflow | Complete | Expo SDK 57 development client, projection, item management, optimizer Apply/Undo |
| 5. Automated quality gates | Complete | Backend tests, Playwright E2E, web lint/build, mobile typecheck/Expo Doctor/export |
| 6. Production persistence | In progress | Render PostgreSQL Blueprint prepared; hosted database and migration rehearsal remain |
| 7. Production operations | In progress | Request IDs, safe logs, backup/restore scripts; hosted monitoring remains |
| 8. Public release | Planned | Staging deployment, security review, app-store release, public demo decision |

## Locked Release Decisions

- Hosting: Render Web Service, Static Site, and PostgreSQL.
- Audience: portfolio demo for recruiters and managers first.
- Data: separate synthetic demo environment and isolated staging environment.
- Contract: US/USD, cents, US federal holidays, America/New_York, 90-day horizon.
- Recommendations: advisory hypothetical bill-date changes with explicit Apply/Undo.

See [docs/DECISIONS.md](DECISIONS.md) for the rationale, acceptance criteria, and remaining release blockers.

## Verified Quality Gates

- Backend: `40` tests passing.
- Web: ESLint passing.
- Web: production build passing.
- Browser: Playwright critical workflow passing locally and enforced in GitHub Actions; separate staging mode targets the Render URLs with synthetic accounts and no local servers.
- Mobile: TypeScript passing.
- Mobile: Expo Doctor `21/21` checks passing.
- Mobile: web, iOS, and Android exports passing.
- Database: fresh Alembic baseline migration passing.
- Operations: SQLite backup/restore smoke test passing.

## What Is Working

- Daily balance projection over 90 days.
- Web projection chart derived from the returned daily balances, including negative-day markers.
- Correct distinction between biweekly and semi-monthly recurrence.
- US weekend and federal holiday settlement rules.
- `FIXED`, `WINDOW`, and `FLEXIBLE` bill constraints.
- Variable bill high-end variance projection.
- Negative-day detection with event-level detail.
- Greedy constrained optimizer with explainable recommendations.
- Reversible hypothetical schedule overrides.
- Authenticated user ownership isolation.
- Web and iPhone development-client workflows using the same API.

## Next Three Deliverables

1. Provision a staging PostgreSQL database and run Alembic migrations against it.
2. Deploy the API and web client to staging with production-style secrets and CORS.
3. Add hosted logs, error tracking, uptime checks, and backup scheduling.

## Staging Preparation Checkpoint

- Added `render.yaml` for separate `cash-flow-simulator-staging-api`, `cash-flow-simulator-staging-web`, and `cash-flow-simulator-staging-db` resources.
- The API is built from the existing Dockerfile; its Blueprint binds PostgreSQL `connectionString`, generates `AUTH_SECRET`, and sets `ENVIRONMENT=staging`.
- The static site runs `npm ci && npm run build`, publishes `dist`, and receives the staging API HTTPS origin through `VITE_API_URL`.
- `CORS_ORIGINS` is set to the default staging static-site origin. Service renames and custom domains require manually updating both URL values in Render.
- No Render credentials, database URLs, or secrets were added to the repository. The current deployed staging URLs were verified with the staging E2E workflow on 2026-08-24.

## Staging E2E Verification

The local and staging browser workflows are intentionally separate:

```powershell
# Local: starts temporary API and Vite servers on alternate ports.
$env:E2E_BACKEND_PORT = '8100'
$env:E2E_FRONTEND_PORT = '5174'
npm run e2e

# Staging: does not start local servers and uses only synthetic data.
$env:STAGING_WEB_URL = 'https://cash-flow-simulator-staging-web.onrender.com'
$env:STAGING_API_URL = 'https://cash-flow-simulator-staging-api.onrender.com'
npm run e2e:staging
```

`STAGING_WEB_URL` is required. `STAGING_API_URL` is optional; when supplied, the staging config checks its public `/health` endpoint before running the browser workflow. Current Render URLs are the web origin `https://cash-flow-simulator-staging-web.onrender.com` and API origin `https://cash-flow-simulator-staging-api.onrender.com`.

## Production Readiness Gaps

- Hosted PostgreSQL provisioning and backup/restore rehearsal.
- Deployment observability and alerting integration.
- Mobile dependency audit review without downgrading Expo SDK 57.
- Broader real-device regression testing.
- App Store release metadata and support/privacy pages.
- Public demo hosting and repository visibility decision.

## Scope Guardrails

Intentionally excluded from v1: Plaid/bank sync, transaction categorization, net worth, debt payoff, investment forecasting, household collaboration, and AI-generated financial advice.

Recommendations are planning scenarios, not payment actions. Projections are estimates, not financial advice.

## How To Contribute Or Review

- `master` is the stable portfolio branch.
- `test-com/development` is the active implementation branch.
- Every development change should include focused validation and update this progress document when a phase changes.
- Use the GitHub issue templates for progress updates and blockers.

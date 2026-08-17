# Project Progress

**Project:** Cashflow Simulator  
**Owner:** MScott  
**Repository:** [github.com/mscott9160-web/cash-flow-simulator](https://github.com/mscott9160-web/cash-flow-simulator)  
**Development branch:** `test-com/development`  
**Stable branch:** `master`

## One-Line Summary

A daily cash-flow simulator that identifies negative-balance days and searches for one constrained bill-scheduling change that could improve them.

## Current Status

**Overall:** Core product complete; production infrastructure in progress  
**Last verified:** 2026-08-17  
**Latest development commit:** `510d778`  
**Stable portfolio commit:** `e43cf4a`

## Delivery Board

| Phase | Status | Evidence |
| --- | --- | --- |
| 1. Projection engine | Complete | Recurrence, holidays, settlement shifts, decimal balances, 40 backend tests |
| 2. FastAPI and persistence | Complete | Auth, ownership, CRUD, SQLite, Alembic, SQLAlchemy, PostgreSQL URL support |
| 3. Web product workflow | Complete | Login, setup, projection, item CRUD, pause/resume, optimizer, Apply/Undo |
| 4. Mobile product workflow | Complete | Expo SDK 57 development client, projection, item management, optimizer Apply/Undo |
| 5. Automated quality gates | Complete | Backend tests, Playwright E2E, web lint/build, mobile typecheck/Expo Doctor/export |
| 6. Production persistence | In progress | PostgreSQL-ready; hosted database and migration rehearsal remain |
| 7. Production operations | In progress | Request IDs, safe logs, backup/restore scripts; hosted monitoring remains |
| 8. Public release | Planned | Staging deployment, security review, app-store release, public demo decision |

## Verified Quality Gates

- Backend: `40` tests passing.
- Web: ESLint passing.
- Web: production build passing.
- Browser: Playwright critical workflow passing.
- Mobile: TypeScript passing.
- Mobile: Expo Doctor `21/21` checks passing.
- Mobile: web, iOS, and Android exports passing.
- Database: fresh Alembic baseline migration passing.
- Operations: SQLite backup/restore smoke test passing.

## What Is Working

- Daily balance projection over 90 days.
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
3. Add hosted logs, error tracking, uptime checks, backup scheduling, and a staging E2E run.

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

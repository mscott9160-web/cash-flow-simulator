# Project Progress

**Project:** Cashflow Simulator  
**Owner:** MScott  
**Repository:** [github.com/mscott9160-web/cash-flow-simulator](https://github.com/mscott9160-web/cash-flow-simulator)  
**Development branch:** `test-com/development`  
**Stable branch:** `master`

## One-Line Summary

A daily cash-flow simulator that identifies negative-balance days and searches for one constrained bill-scheduling change that could improve them.

## Current Status

**Overall:** Core product complete; stable portfolio release published, public-production hardening deferred
**Last verified:** 2026-09-12
**Latest development commit:** `682596c`
**Stable portfolio commit:** `e0b59db`

## Delivery Board

| Phase | Status | Evidence |
| --- | --- | --- |
| 1. Projection engine | Complete | Recurrence, holidays, settlement shifts, decimal balances, 44 backend tests |
| 2. FastAPI and persistence | Complete | Auth, ownership, CRUD, SQLite, Alembic, SQLAlchemy, PostgreSQL URL support |
| 3. Web product workflow | Complete | Login, setup, projection, item CRUD, pause/resume, optimizer, Apply/Undo |
| 4. Mobile product workflow | Complete | Expo SDK 57 development client, projection, item management, optimizer Apply/Undo |
| 5. Automated quality gates | Complete | Backend tests, Playwright E2E, web lint/build, mobile typecheck/Expo Doctor/export |
| 6. Production persistence | Decided for current audience | PostgreSQL 18 backup/restore rehearsal passed locally; staging remains synthetic-only until Render-managed backup/PITR is approved |
| 7. Production operations | In progress | Request IDs, safe logs, auth rate limiting, PostgreSQL rehearsal runbook, dependency audit, policy/support drafts, observability runbook, and scheduled staging health checks; hosted alert ownership remains |
| 8. Public release | Deferred | App Store/TestFlight metadata, public demo decision, and provider-level production controls |

## Approved Release Audience

The current release is ready for:

- Portfolio demonstration.
- Recruiter and manager review.
- Synthetic staging users.
- Internal iOS testing.
- Stable `master` deployment.

The current release is not approved for real financial data or broad public production until these provider-level gates are complete:

- Render-managed backup and point-in-time recovery decision.
- Hosted monitoring and named alert ownership.
- Synthetic staging failure drill.
- Final owner details for privacy, terms, support, and retention.
- Android physical-device testing.
- TestFlight/App Store metadata and release preparation.

The executable team stories for these gates are tracked in [RELEASE-READINESS-BACKLOG.md](RELEASE-READINESS-BACKLOG.md). Product scope is frozen while these stories are being completed.

## Locked Release Decisions

- Hosting: Render Web Service, Static Site, and PostgreSQL.
- Audience: portfolio demo for recruiters and managers first.
- Data: separate synthetic demo environment and isolated staging environment.
- Contract: US/USD, cents, US federal holidays, America/New_York, 90-day horizon.
- Recommendations: advisory hypothetical bill-date changes with explicit Apply/Undo.

See [docs/DECISIONS.md](DECISIONS.md) for the rationale, acceptance criteria, and remaining release blockers.

## Verified Quality Gates

- Backend: `44` tests passing, including auth abuse-limit coverage.
- Web: ESLint passing.
- Web: production build passing.
- Browser: Playwright critical workflow passing locally and enforced in GitHub Actions; separate staging mode targets the Render URLs with synthetic accounts and no local servers.
- Mobile: TypeScript passing.
- Mobile: Expo Doctor `21/21` checks passing.
- Mobile: web, iOS, and Android exports passing.
- Mobile: EAS iOS staging build finished and physical-device acceptance passed on 2026-09-12, including authentication, projection, bill flexibility, optimizer Apply/Undo, Settings/export/delete, retry, and session persistence.
- Mobile: Android staging APK build finished on 2026-09-12; physical Android validation is deferred because no Android device/account is currently available.
- Database: fresh Alembic baseline migration passing.
- Operations: SQLite backup/restore smoke test passing; PostgreSQL backup/restore rehearsal runbook published.
- Dependencies: web and Python production audits report no known vulnerabilities; mobile transitive findings are documented without an Expo-breaking force downgrade.

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
- Web Assumptions view and mobile tab navigation expose the locked product contract in-product.

## Next Three Deliverables

1. Keep the stable portfolio deployment available for review and synthetic staging use.
2. Decide whether to fund Render-managed backup/PITR and configure hosted alert ownership.
3. Complete Android/TestFlight release work only if public or broader internal distribution is desired and the required devices/accounts are available.

## Staging Preparation Checkpoint

- Added `render.yaml` for separate `cash-flow-simulator-staging-api`, `cash-flow-simulator-staging-web`, and `cash-flow-simulator-staging-db` resources.
- The API is built from the existing Dockerfile; its Blueprint binds PostgreSQL `connectionString`, generates `AUTH_SECRET`, and sets `ENVIRONMENT=staging`.
- The static site runs `npm ci && npm run build`, publishes `dist`, and receives the staging API HTTPS origin through `VITE_API_URL`.
- `CORS_ORIGINS` is set to the default staging static-site origin. Service renames and custom domains require manually updating both URL values in Render.
- No Render credentials, database URLs, or secrets were added to the repository. The current deployed staging URLs were verified with the staging E2E workflow after commit `b648f46`.

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

- Hosted PostgreSQL backup/restore rehearsal passed against a local PostgreSQL 18 restore target; managed backup policy verification remains provider-dependent.
- Operations decision: current Render Free-plan staging remains synthetic-only; see [OPERATIONS-DECISION.md](OPERATIONS-DECISION.md).
- Confirm whether Render runs one or multiple API instances; process-local rate limiting is only sufficient for one instance.
- Deployment observability and alerting integration.
- Mobile dependency audit review without downgrading Expo SDK 57.
- Broader real-device regression testing beyond the completed iOS staging acceptance pass.
- Account-level export and deletion workflow is implemented and covered by local and hosted E2E.
- Owner review and publication of privacy, terms, retention, and support drafts.
- Configure hosted monitoring, alert routing, retention, and complete the synthetic staging failure drill.
- Public demo hosting and repository visibility decision.

## Scope Guardrails

Intentionally excluded from v1: Plaid/bank sync, transaction categorization, net worth, debt payoff, investment forecasting, household collaboration, and AI-generated financial advice.

Recommendations are planning scenarios, not payment actions. Projections are estimates, not financial advice.

## How To Contribute Or Review

- `master` is the stable portfolio branch.
- `test-com/development` is the active implementation branch.
- Every development change should include focused validation and update this progress document when a phase changes.
- Use the GitHub issue templates for progress updates and blockers.

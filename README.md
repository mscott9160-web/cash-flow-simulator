# Cashflow Simulator

Daily cash-flow projection for people who have enough money across the month but still risk going negative on a specific day.

[![CI](https://github.com/mscott9160-web/cash-flow-simulator/actions/workflows/ci.yml/badge.svg)](https://github.com/mscott9160-web/cash-flow-simulator/actions/workflows/ci.yml) [![Development](https://img.shields.io/badge/development-test--com%2Fdevelopment-38654C)](https://github.com/mscott9160-web/cash-flow-simulator/tree/test-com/development) [![Stable](https://img.shields.io/badge/stable-master-20251F)](https://github.com/mscott9160-web/cash-flow-simulator/tree/master)

**Progress:** [View the portfolio progress board](docs/PROGRESS.md) · [Read the release decisions](docs/DECISIONS.md)

> Given what you make and what you owe, show which days go negative and what single scheduling change could improve them.

## Why This Project

Monthly budgets hide timing risk. Cashflow models the account balance day by day, applies real settlement behavior, and searches only the obligations that are actually movable. A mortgage should never appear as an optimizer suggestion just because moving it would improve a chart.

## What It Does

- Projects daily balances over a 90-day horizon.
- Distinguishes biweekly pay from semi-monthly pay.
- Shifts income and bill posting dates around weekends and US federal holidays.
- Models bills as `FIXED`, `WINDOW`, or `FLEXIBLE`.
- Projects variable bills at a clearly labeled high-end variance.
- Finds negative days and the events behind them.
- Searches valid business-day candidates and returns an explainable single-change recommendation.
- Supports reversible hypothetical schedule overrides.
- Works through both a React web client and an Expo mobile client.

## Stack

| Layer | Technology |
| --- | --- |
| Web | React 19, Vite, TypeScript |
| Mobile | Expo SDK 57, React Native 0.86 |
| API | Python, FastAPI, Pydantic |
| Domain | Pure Python projection and optimizer engine |
| Storage | SQLite locally, Alembic migrations, PostgreSQL-ready architecture |
| Quality | Pytest, Playwright, ESLint, TypeScript, Expo Doctor |

## Architecture

```text
web (React/Vite) -------\
                         +-- FastAPI /api/v1 -- SQLite/PostgreSQL
mobile (Expo) ----------/          |
                                    +-- backend/core
                                        recurrence
                                        business-day policy
                                        projection fold
                                        constrained optimizer
```

The projection engine has no FastAPI imports or database dependencies. Both clients consume the same API contract; financial rules are not duplicated in JavaScript.

## Run The Web App

From the repository root, install the backend dependencies once:

```powershell
python -m pip install -r backend/requirements.txt
```

Start the API in one terminal:

```powershell
$env:AUTH_SECRET = 'local-development-auth-secret-32-bytes'
$env:DATABASE_PATH = Join-Path $PWD 'cashflow-local.sqlite'
$env:CORS_ORIGINS = 'http://localhost:5173'
$env:ENVIRONMENT = 'development'
python -m uvicorn backend.api:app --host localhost --port 8000
```

Start the web client in another:

```powershell
$env:VITE_API_URL = 'http://localhost:8000'
npm install
npm run dev -- --host localhost --port 5173
```

Open `http://localhost:5173`.

## Run The Mobile App

The mobile app uses an Expo development build, matching the working Fade Society setup. It is not intended to run in an older public Expo Go binary.

```powershell
cd mobile
npm install
$env:EXPO_PUBLIC_API_URL = 'http://192.168.1.183:8000'
npx expo start --dev-client --lan
```

For a physical device, use the computer's LAN address and keep the phone and computer on the same Wi-Fi network. See [mobile/README.md](mobile/README.md) for EAS development-build setup.

## Verification

```powershell
# Web
npm run lint
npm run build

# Backend
python -m pytest backend/tests

# Browser workflow
npx playwright install chromium
npm run e2e

# Mobile
cd mobile
npm run typecheck
npx expo-doctor
npm run export
```

The current checkpoint has 38 backend tests passing, a passing Playwright critical workflow, a clean web build/lint, and Expo Doctor reporting 21/21 checks passed.

## API Surface

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- Account, income, and bill CRUD under `/api/v1/accounts`
- `GET /api/v1/accounts/{account_id}/projection`
- `GET /api/v1/accounts/{account_id}/optimization`
- Reversible override create/list/delete endpoints
- Public `GET /health` and `GET /ready`

## Persistence And Operations

The API reads `DATABASE_URL`, `DATABASE_PATH`, `CORS_ORIGINS`, `AUTH_SECRET`, and `ENVIRONMENT`. `DATABASE_URL` takes precedence and accepts SQLAlchemy URLs such as `postgresql+psycopg://user:password@host/database`; when it is unset, local SQLite uses `DATABASE_PATH` or `cashflow.db`. Production requires an explicit `AUTH_SECRET`. Requests receive an `X-Request-ID`; logs contain request metadata only, not credentials or financial payloads.

The default compose setup remains SQLite. To start the optional local PostgreSQL service, run `docker compose --profile postgres up postgres`, then point the backend at its URL, for example `DATABASE_URL=postgresql+psycopg://cashflow:cashflow-local-only@localhost:5432/cashflow`. Run `alembic upgrade head` against the selected database before starting a production deployment. Alembic uses the same `DATABASE_URL` precedence as the API.

SQLite backup and restore utilities are in `scripts/backup_sqlite.py` and `scripts/restore_sqlite.py`. Stop the API before restoring a live database.

## Scope Boundary

This is a focused cash-flow planning tool. Bank syncing, Plaid, categorization, net worth, debt payoff, investment forecasting, and AI-generated financial advice are intentionally outside v1.

Projections are estimates, not financial advice. Users should verify actual posting dates and account balances with their financial institution.

## Project Status

The web and mobile core workflows are implemented. Remaining production work includes hosted PostgreSQL operations, deployment observability integration, dependency audit remediation, store-release preparation, and broader real-device testing.

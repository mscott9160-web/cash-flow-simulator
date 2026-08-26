# PostgreSQL Backup and Restore Rehearsal

This runbook rehearses a logical backup and restore of the Render PostgreSQL database. Perform it against a disposable restore database first. Do not paste connection strings or secrets into the repository, chat, or shell history.

## Prerequisites

- `pg_dump`, `pg_restore`, and `psql` from a PostgreSQL client matching the database major version.
- A database connection string copied from the Render dashboard and a separate empty restore database.
- A maintenance window or a quiet application period. Logical dumps are consistent, but restoring over a live target is not safe.

## Backup

PowerShell:

```powershell
$env:PGSOURCE = 'postgresql://<source-connection-string>'
$backup = Join-Path $PWD "backups\cashflow-$(Get-Date -Format yyyyMMdd-HHmmss).dump"
New-Item -ItemType Directory -Force (Split-Path $backup) | Out-Null
pg_dump --format=custom --no-owner --file=$backup $env:PGSOURCE
pg_restore --list $backup | Select-Object -First 10
```

Record the dump file size and SHA-256 checksum in the incident or change record:

```powershell
Get-FileHash $backup -Algorithm SHA256
```

## Restore rehearsal

Restore into an empty disposable database, not the source database:

```powershell
$env:PGTARGET = 'postgresql://<disposable-restore-connection-string>'
psql $env:PGTARGET -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'
pg_restore --exit-on-error --no-owner --dbname=$env:PGTARGET $backup
python -m alembic upgrade head
```

Validate the restored database through the API using a temporary `DATABASE_URL`, then remove that environment variable when finished:

```powershell
$env:DATABASE_URL = $env:PGTARGET
python -c "from backend.storage import ScenarioStore; ScenarioStore().check_ready(); print('database ready')"
Remove-Item Env:DATABASE_URL
```

Confirm `/ready`, registration/login, account export, and a representative projection. Compare row counts for `users`, `accounts`, `items`, and `overrides` with the source. Delete the disposable database after the rehearsal.

## Render dashboard follow-up

Render dashboard access is required to confirm automated backup retention, point-in-time recovery availability, alerting, database access permissions, and the actual production/staging connection string. These settings cannot be verified from this repository.

## Auth deployment note

Registration and login use a process-local per-IP limiter configured by `AUTH_RATE_LIMIT_MAX_ATTEMPTS` and `AUTH_RATE_LIMIT_WINDOW_SECONDS`. This is useful for a single API instance and is intentionally dependency-free. For multiple API instances, configure an edge/WAF or shared rate-limit store before treating this as a distributed control.
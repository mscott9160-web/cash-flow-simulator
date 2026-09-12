# Data Retention Draft

**Status:** Owner review and provider configuration required.
**Last updated:** 2026-09-11

## Application Data

Active account data is retained while the account exists so the user can reopen and update a projection. Account deletion removes the account, saved income and bills, and hypothetical overrides from the application database.

## Backups and Logs

Database backups, deployment logs, request metadata, and error-tracking records may persist after account deletion according to their configured retention periods. The owner must configure and publish exact periods before real-data testing. Logs must not contain passwords, bearer tokens, or financial payloads.

## Recovery and Access

Backups are for service recovery and must be access-controlled. The PostgreSQL backup/restore rehearsal is documented in [POSTGRES-BACKUP-RESTORE-REHEARSAL.md](POSTGRES-BACKUP-RESTORE-REHEARSAL.md). Restore databases used for rehearsal must contain synthetic data only and must be destroyed after verification.

## Owner Review Items

Set and document database-backup retention, log retention, error-tracking retention, deletion propagation timing, access owners, and the process for handling a legal retention requirement.

# Observability and Alerting Runbook

**Status:** Configuration and failure drill required before invited real-data testing.
**Last updated:** 2026-09-11

## Service Checks

Monitor both public API endpoints from outside the Render network:

- `GET /health` confirms the process is responding.
- `GET /ready` confirms the database connection is usable.

Expected response: HTTP `200` with `{"status":"ok"}` or `{"status":"ready"}`. Alert after three consecutive failures or a sustained failure of five minutes. Keep the two checks separate so a live process with an unavailable database is visible.

## Application Alerts

Create alerts for:

- API 5xx rate above 2% for five minutes.
- Any failed migration or container startup.
- Database readiness failures.
- Authentication 401/429 volume above the expected synthetic-staging baseline.
- Export or deletion endpoint failures.
- Backup job failure or missed backup window.

Every alert needs a named owner, notification destination, runbook link, and severity. Test at least one synthetic alert before inviting real-data users.

## Request Correlation and Redaction

The API emits an `X-Request-ID` response header and logs method, path, status, duration, and request ID. Monitoring must retain these fields so a user-visible error can be traced without storing account payloads.

Never forward passwords, bearer tokens, database URLs, request bodies, financial amounts, email addresses, or exported account data to an observability provider. Review provider default request logging and disable body capture.

## Retention and Access

The owner must configure and record log, uptime, error-event, and alert-history retention periods. Restrict access to operators who need it, enable MFA on the provider account, and document who receives alerts.

## Staging Failure Drill

Use synthetic staging data only:

1. Confirm `/health` and `/ready` are green.
2. Temporarily make a disposable staging check fail or pause the API service through the provider dashboard.
3. Verify the uptime alert fires and reaches the named owner.
4. Restore the service and verify recovery notification.
5. Record timestamps, alert delivery, response time, and any false positives.
6. Remove temporary monitors or test routing after the drill.

Do not induce failures in a production database or expose credentials in monitor definitions.

## Render Configuration Inputs

Render dashboard access is required to configure log retention, service notifications, database backup alerts, uptime monitoring, and team access. These settings are intentionally not encoded in `render.yaml` because provider credentials, recipients, and retention choices are owner-controlled inputs.

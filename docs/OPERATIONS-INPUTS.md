# Operations Decision Options

Use this sheet to close the remaining provider and owner decisions. Do not put passwords, database URLs, API keys, or tokens in this file.

## 1. Monitoring Provider

**Recommended for the current portfolio/staging audience:** use Render health checks plus GitHub Actions scheduled staging health checks. Add a paid external uptime/error provider only when real-data or public production use is approved.

Options:

- **A: Render + GitHub Actions only.** Lowest cost. Suitable for synthetic portfolio staging. Limited alert routing and history.
- **B: Add an external uptime provider.** Better independent monitoring for `/health`, `/ready`, and the web origin. Requires selecting a provider and notification destination.
- **C: Add hosted error tracking.** Best for public production diagnosis. Requires a provider, DSN/configuration, redaction review, and retention decision.

Decision needed: `A`, `B`, or `C`.

## 2. Alert Owner and Destination

**Recommended default:** the project owner receives alerts by email, with a second technical contact added before real-data testing.

Options:

- **A: Owner email only.** Appropriate for portfolio staging.
- **B: Owner email plus technical backup.** Recommended for invited testers.
- **C: Team channel plus email escalation.** Recommended for public production.

Decision needed: owner name, destination, and backup contact. Do not record credentials here.

## 3. Log and Alert Retention

**Recommended synthetic-staging default:** 7 days for logs and alert history, with no request-body capture.

Options:

- **A: 7 days.** Lowest retention and adequate for portfolio staging.
- **B: 30 days.** Better for invited testers and incident investigation.
- **C: 90 days or provider default.** Only after privacy/legal review.

Decision needed: log retention, error-event retention, and alert-history retention.

## 4. Render Service Scale

**Recommended now:** keep one API instance. The current auth limiter is process-local and is sufficient only for one instance.

Options:

- **A: One API instance.** Lowest cost and compatible with current limiter.
- **B: Multiple instances with edge/WAF rate limiting.** Required before horizontal scaling.
- **C: Multiple instances with a shared rate-limit store.** Stronger control but adds infrastructure.

Decision needed: keep one instance or fund distributed rate limiting before scaling.

## 5. Policy Owner Details

Required before real financial data:

- Legal operator identity.
- Effective date.
- Support email or ticket URL.
- Expected response window.
- Jurisdiction/governing law if required.
- Application-data retention period.
- Backup retention period.
- Log/error-event retention period.
- Deletion propagation timing.
- Hosting/subprocessor disclosure.

**Recommended current decision:** keep policy drafts unpublished and synthetic-only until these values are reviewed and approved.

## Current Recommended Posture

For the approved audience of portfolio reviewers, recruiter/manager reviewers, synthetic staging users, internal iOS testers, and stable `master` deployment:

- Monitoring: `A`, Render + GitHub Actions.
- API scale: one instance.
- Logs/alerts: 7 days, no request bodies.
- Alerts: owner email only.
- Data: synthetic-only.
- Public production and real financial data: blocked until owner/provider decisions are complete.

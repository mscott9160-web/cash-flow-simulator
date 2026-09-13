# Provider Execution Checklist

This checklist covers the remaining manual stories after the stable portfolio release. Use synthetic staging data only. Never commit database URLs, passwords, API keys, or personal legal details.

## Story A: Configure Render Notifications

**Goal:** route staging alerts to the owner's private email.

1. Sign in to Render.
2. Open `cash-flow-simulator-staging-api`.
3. Open service settings, notifications, or alerting.
4. Enable notifications for deploy failure, service failure, repeated 5xx responses, and readiness failure if available.
5. Set the notification destination to the owner's private email.
6. Open `cash-flow-simulator-staging-db`.
7. Enable database availability, backup, and recovery notifications if the current plan exposes them.
8. Set the same owner email destination.
9. Confirm that request bodies, passwords, bearer tokens, database URLs, and financial payloads are not included in logs or provider captures.
10. Record the configured retention as 7 days where the provider permits it.

**Evidence:** screenshots or provider notes with the email address redacted.

**Stop condition:** if the Free plan does not expose a notification or retention setting, record `not available on current plan` and keep staging synthetic-only.

## Story B: Run the Synthetic Staging Failure Drill

**Goal:** prove that a staging failure reaches the owner and recovers.

1. Confirm `https://cash-flow-simulator-staging-api.onrender.com/health` returns `{"status":"ok"}`.
2. Confirm `/ready` returns `{"status":"ready"}`.
3. Open the API service in Render.
4. Use a disposable staging action such as pausing/restarting the service, only if the dashboard provides a reversible control.
5. Record the UTC start time.
6. Verify the owner email receives the failure alert.
7. Record the alert time and any provider request ID.
8. Restore/restart the service.
9. Verify `/health` and `/ready` return success again.
10. Record recovery time and whether a recovery notification arrived.
11. Remove any temporary monitor or test routing.

**Evidence:** redacted timestamps, alert delivery, and recovery result.

**Stop condition:** do not deliberately damage the database or delete the staging service. If no safe reversible failure control exists, stop and record the drill as blocked by provider capabilities.

## Story C: Complete Policy Owner Inputs

**Goal:** replace draft placeholders before any real financial data is accepted.

Complete these privately with the project owner:

- Legal operator identity.
- Effective date.
- Support email or ticket URL.
- Expected response window.
- Jurisdiction/governing law.
- Application-data retention period.
- Backup retention period.
- Log/error-event retention period.
- Deletion propagation timing.
- Hosting/subprocessor disclosure.

Then update and approve:

- `docs/PRIVACY.md`
- `docs/TERMS.md`
- `docs/DATA-RETENTION.md`
- `docs/SUPPORT.md`

**Stop condition:** do not publish or accept real financial data while any required owner input is blank or unapproved.

## Story D: Android Validation Deferred

**Current status:** Android APK is built, but no Android device/account is available.

When a device becomes available:

1. Open the EAS Android build link from the release backlog.
2. Install the internal APK.
3. Use cellular or a separate Wi-Fi network.
4. Verify login, account setup, projection, negative-day detail, bill flexibility, Apply/Undo, Settings/export/delete, retry, sign out, and session persistence.
5. Record device model, Android version, build ID, and results.

Until then, keep Android physical-device validation marked deferred. This does not block portfolio use, synthetic staging, or internal iOS testing.

## Story E: TestFlight/App Store Deferred

**Current status:** internal iOS EAS build passed physical acceptance; public distribution is not approved.

When public or broader internal iOS distribution is desired:

1. Confirm Apple Developer account and App Store Connect access.
2. Confirm app name, bundle ID, version, build number, and environment.
3. Add approved privacy URL, terms URL, support URL, and account-deletion disclosure.
4. Prepare screenshots and store description.
5. Create a production/internal EAS profile pointing at the approved API environment.
6. Build and upload to TestFlight.
7. Test the release candidate with an internal tester.
8. Do not submit publicly until provider recovery, monitoring, policy, and support gates are accepted.

## Current Stop/Go Rule

**Go now:** portfolio demos, recruiter/manager review, synthetic staging users, internal iOS testing, stable master deployment.

**Stop:** real financial data, public production, and public app-store distribution until the provider and owner-input stories above are complete.

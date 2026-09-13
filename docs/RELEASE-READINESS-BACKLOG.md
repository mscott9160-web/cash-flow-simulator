# Release Readiness Backlog

**Release target:** Broader production readiness after the stable portfolio release
**Scope rule:** Do not add new product functionality during this phase. The projection chart/list, account workflows, optimizer, web client, mobile client, and current US/USD planning contract are frozen.
**Current stable branch:** `master`
**Current development branch:** `test-com/development`

## Story 1: Decide Render Backup and PITR

**Owner:** Product owner + technical lead
**Priority:** Critical
**Status:** Ready to start

**Story**

As the service owner, I need a documented Render database recovery decision so I know whether the service can recover from data loss before allowing real financial data.

**Acceptance criteria**

- Review the current Render PostgreSQL plan and confirm whether managed backups are enabled.
- Record backup retention, point-in-time recovery availability, region, database version, access owners, RPO, and RTO.
- Choose one path: upgrade Render for managed recovery, or keep the environment synthetic-only and document the limitation.
- Link the successful PostgreSQL 18 logical backup/restore rehearsal and checksum evidence.
- No real financial data is used during testing.

**Evidence**

- Render plan/recovery screenshots or dashboard notes.
- Completed [POSTGRES-BACKUP-RESTORE-REHEARSAL.md](POSTGRES-BACKUP-RESTORE-REHEARSAL.md).
- Recorded RPO/RTO decision.

**Definition of done**

The release decision is written down and a reviewer can identify exactly what happens after database loss.

## Story 2: Configure Monitoring and Alert Ownership

**Owner:** Technical lead + operations owner
**Priority:** Critical
**Status:** Ready to start

**Story**

As the service owner, I need health, error, authentication, and database alerts assigned to named people so failures are detected and acted on.

**Acceptance criteria**

- Monitor API `/health` and `/ready`.
- Monitor the staging web origin.
- Configure alerts for elevated 5xx responses, readiness failures, authentication abuse, export/delete failures, migration failures, and backup failures.
- Assign a named owner and notification destination for every alert.
- Configure log, error-event, and alert-history retention.
- Confirm sensitive data, passwords, bearer tokens, and financial payloads are not captured.
- Link each alert to [OBSERVABILITY.md](OBSERVABILITY.md).

**Evidence**

- Provider monitor configuration.
- Alert routing screenshot or exported settings.
- Named owner and retention record.

**Definition of done**

A service failure produces an actionable alert with an owner and a runbook link.

## Story 3: Run the Synthetic Staging Failure Drill

**Owner:** Operations owner + QA
**Priority:** High
**Status:** Blocked by Story 2

**Story**

As the service owner, I need to prove that a staging outage is detected and recovered without exposing real data.

**Acceptance criteria**

- Use synthetic staging data only.
- Record healthy `/health` and `/ready` responses before the drill.
- Cause a disposable staging failure using the provider dashboard.
- Verify the alert reaches the named owner.
- Restore the service and verify the recovery alert.
- Record outage start, alert time, recovery time, false positives, RPO, and RTO.
- Remove temporary monitors or test routing.

**Evidence**

- Drill timestamp record.
- Alert delivery evidence.
- Recovery result and follow-up actions.

**Definition of done**

The team can detect, communicate, and recover from a staging failure using a documented procedure.

## Story 4: Finalize Privacy, Terms, Support, and Retention Details

**Owner:** Product owner
**Priority:** Critical for real-data testing
**Status:** Blocked by owner inputs

**Story**

As a user, I need to understand who operates the service, what data is stored, how long it is retained, and how to request help or deletion.

**Acceptance criteria**

- Add legal operator identity and effective dates.
- Add support email or ticket URL and expected response window.
- Add jurisdiction and governing-law decisions where required.
- Set exact application, backup, log, and error-tracking retention periods.
- Document export and account deletion timing, including backup implications.
- Document hosting/subprocessors required for the intended audience.
- Publish or link the reviewed policies from the web Settings surface and release documentation.
- Do not permit real financial data until owner review is complete.

**Evidence**

- Approved [PRIVACY.md](PRIVACY.md), [TERMS.md](TERMS.md), [DATA-RETENTION.md](DATA-RETENTION.md), and [SUPPORT.md](SUPPORT.md).
- Published URLs or release-approved documents.

**Definition of done**

A real-data tester can identify the operator, support path, retention policy, export behavior, and deletion behavior before using the service.

## Story 5: Test Android on a Physical Device

**Owner:** Mobile owner + QA
**Priority:** High for broader mobile distribution
**Status:** Deferred: no Android device/account available

**Story**

As an Android tester, I need the internal build to work away from the developer LAN with the hosted HTTPS API.

**Acceptance criteria**

- Install an internal Android build on a physical device.
- Verify login/register, account setup, projection, negative-day detail, bill flexibility, optimizer Apply/Undo, Settings/export/delete, retry, sign out, and session persistence.
- Test cellular or a separate Wi-Fi network, not only the developer LAN.
- Record device model, Android version, build ID, API environment, and pass/fail results.
- Record and resolve Android-specific failures.

**Evidence**

- EAS build URL and build ID.
- Device test record.
- Screenshots or screen recording where useful.

**Definition of done**

A physical Android tester can complete the critical workflow against the hosted staging API.

**Deferral note**

The internal Android build is complete and available, but physical-device execution is deferred until an Android device and account are available. This does not block the approved portfolio, synthetic-staging, or internal-iOS audiences.

## Story 6: Prepare TestFlight and App Store Metadata

**Owner:** Product owner + mobile owner
**Priority:** Medium until public distribution is approved
**Status:** Deferred: public distribution not approved

**Story**

As an internal iOS tester or future store reviewer, I need an installable build with accurate identity, privacy, support, and release metadata.

**Acceptance criteria**

- Confirm Apple bundle ID, app name, version, build number, and signing configuration.
- Create the intended EAS production or internal distribution profile.
- Prepare app description, screenshots, support URL, privacy URL, terms URL, and account-deletion disclosure.
- Verify the build points to the intended API environment.
- Upload an internal TestFlight build and complete the critical workflow.
- Do not submit publicly until the production gates and policy review are complete.

**Evidence**

- EAS build and submission IDs.
- TestFlight internal tester result.
- App Store Connect metadata checklist.

**Definition of done**

An internal tester can install the intended release build and the store metadata is complete enough for the approved distribution stage.

## Story 7: Rebuild and Distribute the Release Candidate

**Owner:** Release owner + QA
**Priority:** Final gate
**Status:** Blocked by Stories 1-6 as applicable

**Story**

As the release owner, I need a reproducible candidate built from the accepted commit so the distributed app matches the tested source and environment.

**Acceptance criteria**

- Identify the exact source commit and environment.
- Run backend, web, mobile, dependency, local E2E, hosted E2E, and device checks required for the audience.
- Build web, API, and mobile artifacts from the accepted source.
- Confirm release notes and known limitations.
- Confirm synthetic-only or real-data approval status.
- Distribute only through the approved channel: portfolio web, internal iOS, TestFlight, or public store.
- Record rollback and support contacts.

**Evidence**

- Commit SHA.
- CI run URL.
- Hosted E2E result.
- EAS build/submission IDs.
- Release checklist and known-limitations record.

**Definition of done**

The release candidate is traceable, tested for its intended audience, and distributed with no ambiguity about its data or operational limitations.

## Explicitly Deferred Product Work

Do not add these during this release-readiness phase:

- Calendar replacement for the canonical chart/list projection.
- Bank or Plaid connections.
- Budgeting, categorization, or transaction analysis.
- Net worth, debt payoff, or investment forecasting.
- Payment execution or biller integrations.
- Notifications.
- Household collaboration.
- Multi-step optimization or scenario history.

Reopen product scope only after the stable release has been shown to reviewers and feedback has been collected.

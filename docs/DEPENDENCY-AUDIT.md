# Dependency Audit

**Audit date:** 2026-09-11
**Branch:** `test-com/development`

## Web

Command:

```powershell
npm audit --omit=dev --audit-level=high
```

Result: **0 production vulnerabilities reported.**

## Mobile

Command:

```powershell
Push-Location mobile
npm audit --omit=dev --audit-level=high
Pop-Location
```

Result: **15 transitive vulnerabilities reported: 5 high and 10 moderate.** Findings are rooted in the Expo SDK 57 / Metro toolchain, including `image-size`, `js-yaml`, and `uuid` dependency paths.

The automated force fix proposes installing Expo 46, which is a breaking downgrade from the supported Expo SDK 57 development-client setup. Do not run `npm audit fix --force`. This finding remains an explicit release exception until Expo publishes a compatible dependency resolution or the mobile SDK is intentionally upgraded as a coordinated change.

## Python

Command, run with the Python 3.12 interpreter used by CI:

```powershell
python -m pip_audit -r backend/requirements.txt
```

Result: **No known vulnerabilities found.**

## Release Decision

- Web: clean for the audited production dependency set.
- Mobile: high/moderate transitive findings remain; no force downgrade is approved.
- Python: no known vulnerabilities reported by `pip-audit`.
- CI now reruns the web and Python audits on every push and pull request.

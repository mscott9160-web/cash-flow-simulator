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

The repository requires a Python audit tool that is not part of the application environment. `pip-audit` was installed through the managed Python package tool, but it was placed in a different interpreter than the terminal-selected Python 3.12 runtime, so the scan could not be executed from this workspace shell.

Before inviting real-data testers, run the following from the same interpreter used by CI or the deployment build:

```powershell
python -m pip install pip-audit
python -m pip_audit -r backend/requirements.txt
```

Record the result here and in the release checklist. Do not treat the Python audit as complete until the command produces a report.

## Release Decision

- Web: clean for the audited production dependency set.
- Mobile: high/moderate transitive findings remain; no force downgrade is approved.
- Python: pending a scan in the CI/deployment interpreter.

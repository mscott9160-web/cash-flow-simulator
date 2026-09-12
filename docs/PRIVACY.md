# Privacy Notice Draft

**Status:** Owner review required before invited real-data testing.
**Last updated:** 2026-09-11

Cashflow Simulator is a planning tool. It accepts the income, bills, balances, dates, and scheduling assumptions that a user chooses to enter. It does not connect to a bank, import transactions, move money, or execute payments.

## Data We Store

For an authenticated account, the service stores the email address, a password hash, account starting point, saved income and bill rules, enabled or paused state, and hypothetical bill-date overrides. Passwords are not stored in plaintext. Account export contains the account's saved planning data and does not contain password hashes or access tokens.

The local demo uses synthetic data in the browser and does not create an account or send demo data to the API.

## How We Use It

Saved planning data is used to calculate the daily projection and constrained scheduling recommendations requested by the user. Recommendations are hypothetical and do not trigger payments.

## Sharing and Security

Do not enter bank credentials, account numbers, or information that is not needed for the projection. Access to saved account data requires authentication and ownership checks. No policy can promise absolute security; report suspected unauthorized access through the support channel published with this notice.

## Export and Deletion

Settings provides an account-data export. Account deletion permanently removes the account and its saved income, bill, and hypothetical override records from the application database. Backups and operational logs may have separate retention periods; those periods must be configured and published by the owner before real-data testing.

## Owner Review Items

Before publication, the owner must add the legal operator identity, jurisdiction, effective date, support contact, subprocessors or hosting disclosure, backup retention period, and applicable data-subject rights required for the intended audience.

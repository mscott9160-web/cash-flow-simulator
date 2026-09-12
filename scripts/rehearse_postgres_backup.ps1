param(
    [string]$SourceUrl = $env:PGSOURCE,
    [string]$TargetUrl = $env:PGTARGET,
    [string]$Image = 'postgres:16-alpine'
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($SourceUrl) -or [string]::IsNullOrWhiteSpace($TargetUrl)) {
    throw 'Set PGSOURCE and PGTARGET in the local shell, or pass -SourceUrl and -TargetUrl. Never commit these values.'
}

if ($SourceUrl -eq $TargetUrl) {
    throw 'Source and target database URLs must be different. The target must be disposable.'
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker is required because native PostgreSQL client tools were not found.'
}

$backupDirectory = Join-Path $PWD 'backups'
New-Item -ItemType Directory -Force $backupDirectory | Out-Null
$backupName = "cashflow-staging-$(Get-Date -Format yyyyMMdd-HHmmss).dump"
$backupPath = Join-Path $backupDirectory $backupName
$backupMount = (Resolve-Path $backupDirectory).Path

function Invoke-PostgresClient {
    param([string[]]$Arguments)
    & docker run --rm --mount "type=bind,source=$backupMount,target=/backup" $Image @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL client command failed with exit code $LASTEXITCODE."
    }
}

Write-Host 'Checking source database connectivity...'
Invoke-PostgresClient @('psql', $SourceUrl, '-v', 'ON_ERROR_STOP=1', '-c', 'SELECT current_database(), current_user;')

Write-Host "Creating custom-format backup at $backupPath ..."
Invoke-PostgresClient @('pg_dump', '--dbname', $SourceUrl, '--format=custom', '--no-owner', '--no-acl', '--file', "/backup/$backupName")

if (-not (Test-Path $backupPath)) {
    throw "Backup file was not created: $backupPath"
}

Get-Item $backupPath | Select-Object FullName, Length, LastWriteTime
Get-FileHash $backupPath -Algorithm SHA256

Write-Host 'Inspecting backup contents...'
Invoke-PostgresClient @('pg_restore', '--list', "/backup/$backupName")

Write-Warning 'The next command drops and recreates public schema in the disposable target database.'
$confirmation = Read-Host 'Type RESTORE to continue'
if ($confirmation -cne 'RESTORE') {
    throw 'Restore cancelled. The backup remains in the local backups directory for review.'
}

Write-Host 'Resetting disposable target schema...'
Invoke-PostgresClient @('psql', $TargetUrl, '-v', 'ON_ERROR_STOP=1', '-c', 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;')

Write-Host 'Restoring backup...'
Invoke-PostgresClient @('pg_restore', '--dbname', $TargetUrl, '--exit-on-error', '--no-owner', '--no-acl', "/backup/$backupName")

Write-Host 'Verifying restored row counts...'
Invoke-PostgresClient @('psql', $TargetUrl, '-v', 'ON_ERROR_STOP=1', '-c', "SELECT 'users' AS table_name, count(*) FROM users UNION ALL SELECT 'accounts', count(*) FROM accounts UNION ALL SELECT 'items', count(*) FROM items UNION ALL SELECT 'overrides', count(*) FROM overrides;")

Write-Host "Rehearsal complete. Review the counts and checksum, then securely remove $backupPath when evidence is recorded."

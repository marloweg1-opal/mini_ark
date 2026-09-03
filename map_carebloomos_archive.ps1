param(
  [switch]$Execute,
  [int]$OlderThanDays = 60,
  [int]$Limit = 0,
  [string]$TargetRoot = 'R:\RuneScript\Projects\CareBloomOS'
)

$ErrorActionPreference = 'Stop'

$miniArkRoot = 'C:\mini_ark'
$ark = Join-Path $miniArkRoot 'ark.cmd'

if (-not (Test-Path -LiteralPath $ark)) {
  throw "Mini ARK launcher not found: $ark"
}

$argsList = @(
  'carebloom-archive-map',
  '--target-root', $TargetRoot,
  '--older-than-days', [string]$OlderThanDays
)

if ($Limit -gt 0) {
  $argsList += @('--limit', [string]$Limit)
}
if ($Execute) {
  $argsList += '--execute'
}

Push-Location $miniArkRoot
try {
  & $ark @argsList
  if ($LASTEXITCODE -ne 0) {
    throw "Mini ARK CareBloomOS archive map command failed."
  }
} finally {
  Pop-Location
}

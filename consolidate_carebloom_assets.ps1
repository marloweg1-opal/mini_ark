param(
  [switch]$Execute,
  [switch]$UpdateRefs,
  [int]$Limit = 0,
  [string]$CanonicalRoot = 'R:\Projects\CareBloomOS\99_Consolidated_Assets'
)

$ErrorActionPreference = 'Stop'

$miniArkRoot = 'C:\mini_ark'
$ark = Join-Path $miniArkRoot 'ark.cmd'

if (-not (Test-Path -LiteralPath $ark)) {
  throw "Mini ARK launcher not found: $ark"
}

$argsList = @('carebloom-consolidate', '--canonical-root', $CanonicalRoot)
if ($Limit -gt 0) {
  $argsList += @('--limit', [string]$Limit)
}
if ($Execute) {
  $argsList += '--execute'
}
if ($UpdateRefs) {
  $argsList += '--update-refs'
}

Push-Location $miniArkRoot
try {
  & $ark @argsList
  if ($LASTEXITCODE -ne 0) {
    throw "Mini ARK CareBloom consolidation command failed."
  }
} finally {
  Pop-Location
}

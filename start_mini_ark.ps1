param(
  [int]$PreferredPort = 8787,
  [switch]$Open
)

$ErrorActionPreference = 'Stop'

$miniArkRoot = 'C:\mini_ark'
$indexPath = Join-Path $miniArkRoot 'index.html'
$runtimeRoot = Join-Path $miniArkRoot 'logs'

if (-not (Test-Path -LiteralPath $indexPath)) {
  throw "Mini ARK cockpit not found: $indexPath"
}

function Test-PortAvailable {
  param([int]$Port)
  $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse('127.0.0.1'), $Port)
  try {
    $listener.Start()
    return $true
  } catch {
    return $false
  } finally {
    $listener.Stop()
  }
}

function Get-PythonCommand {
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) { return @{ File = $python.Source; Args = @('-m', 'http.server') } }

  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) { return @{ File = $py.Source; Args = @('-3', '-m', 'http.server') } }

  return $null
}

$pythonCommand = Get-PythonCommand
if (-not $pythonCommand) {
  throw 'Python was not found on PATH. Open C:\mini_ark\index.html directly, or install Python to use the local server.'
}

$port = $null
foreach ($candidate in $PreferredPort..($PreferredPort + 10)) {
  if (Test-PortAvailable -Port $candidate) {
    $port = $candidate
    break
  }
}

if (-not $port) {
  throw "No local port was available from $PreferredPort to $($PreferredPort + 10)."
}

$arguments = @($pythonCommand.Args + @([string]$port, '--bind', '127.0.0.1'))
$process = Start-Process -FilePath $pythonCommand.File -ArgumentList $arguments -WorkingDirectory $miniArkRoot -PassThru -WindowStyle Hidden
$url = "http://127.0.0.1:$port/"

$logWritten = $false
try {
  [pscustomobject]@{
    Started = (Get-Date).ToString('o')
    ProcessId = $process.Id
    Url = $url
    Root = $miniArkRoot
    Index = $indexPath
  } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeRoot 'mini_ark_server.json') -Encoding UTF8
  $logWritten = $true
} catch {
  Write-Warning "Mini ARK started, but the server log could not be written: $($_.Exception.Message)"
}

Write-Host "Mini ARK is running."
Write-Host "URL: $url"
Write-Host "Root: $miniArkRoot"
Write-Host "ProcessId: $($process.Id)"
Write-Host "LogWritten: $logWritten"

if ($Open) {
  Start-Process $url
}

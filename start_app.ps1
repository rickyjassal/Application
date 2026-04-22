$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$runPath = Join-Path $projectRoot 'run.py'
$logDir = Join-Path $projectRoot 'logs'
$stdoutLog = Join-Path $logDir 'app_stdout.log'
$stderrLog = Join-Path $logDir 'app_stderr.log'
$port = 5001

if (-not (Test-Path $pythonPath)) {
    throw "Python virtual environment was not found at $pythonPath"
}

if (-not (Test-Path $runPath)) {
    throw "Application entry point was not found at $runPath"
}

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

$listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    Write-Output "Application already listening on port $port."
    exit 0
}

Start-Process -FilePath $pythonPath `
    -ArgumentList $runPath `
    -WorkingDirectory $projectRoot `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -WindowStyle Hidden

Write-Output "Application launch requested."

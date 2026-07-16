param(
    [Parameter(Mandatory = $true)]
    [string]$NavifluxDir,

    [int]$ServerPort = 5000,
    [int]$ClientPort = 5173
)

$ErrorActionPreference = "Stop"

$navifluxRoot = Resolve-Path $NavifluxDir
$serverDir = Join-Path $navifluxRoot "server"
$clientDir = Join-Path $navifluxRoot "client"
$serverPython = Join-Path $serverDir "venv\Scripts\python.exe"
$npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source

if (-not (Test-Path $serverPython)) {
    throw "NAViFluX server venv was not found at $serverPython. Run NAViFluX install first."
}
if (-not $npmCmd) {
    throw "npm.cmd was not found. Install Node.js and make sure it is on PATH."
}

$cacheRoot = Join-Path (Resolve-Path "$PSScriptRoot\..\..") "outputs\external_tools\naviflux_cache"
New-Item -ItemType Directory -Force -Path $cacheRoot | Out-Null

$backendCommand = @"
`$env:LOCALAPPDATA = '$cacheRoot'
`$env:FLASK_APP = 'app.py'
& '$serverPython' -m flask run --host 127.0.0.1 --port $ServerPort
"@

$frontendCommand = @"
& '$npmCmd' run dev -- --host 127.0.0.1 --port $ClientPort
"@

Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "cd '$serverDir'; $backendCommand"
Start-Sleep -Seconds 3
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "cd '$clientDir'; $frontendCommand"

Write-Host "NAViFluX backend:  http://127.0.0.1:$ServerPort"
Write-Host "NAViFluX frontend: http://127.0.0.1:$ClientPort"

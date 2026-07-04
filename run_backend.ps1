# One-command backend runner (Windows). Works from ANY directory, any Python setup:
# creates the project venv, installs deps, loads .env, starts the API.
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot          # always run from the project root

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
}
& ".\venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r requirements.txt

if (-not (Test-Path ".env") -and -not $env:DATABASE_URL) {
    Write-Host "No .env found - starting in DEMO mode (SQLite, no keys needed)." -ForegroundColor Yellow
    Write-Host "For real mode: copy .env.example to .env and fill in your values." -ForegroundColor Yellow
    $env:TESTING = "1"
    if (-not $env:JWT_SECRET) { $env:JWT_SECRET = "dev-demo-secret" }
}

Write-Host "Starting backend on http://localhost:8000 ..." -ForegroundColor Green
& ".\venv\Scripts\python.exe" -m uvicorn backend.main:app --port 8000

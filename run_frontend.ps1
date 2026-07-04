# One-command frontend runner (Windows): installs deps on first run, starts Vite dev server.
$ErrorActionPreference = "Stop"
Set-Location -Path (Join-Path $PSScriptRoot "frontend")
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
    npm install --no-audit --no-fund
}
Write-Host "Starting frontend on http://localhost:5173 ..." -ForegroundColor Green
npm run dev

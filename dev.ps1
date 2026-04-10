# dev.ps1 — Démarre le backend (FastAPI) et le frontend (Vite) dans la même session
# Usage : .\dev.ps1   |   Ctrl+C pour tout arrêter

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# ── Backend ────────────────────────────────────────────────────────────────────
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "venv introuvable : $venvPython`nLance d'abord : python -m venv .venv && pip install -e .[dev]"
}

# ── Frontend ───────────────────────────────────────────────────────────────────
$frontendDir = Join-Path $root "frontend"
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "[frontend] node_modules absent, installation en cours..." -ForegroundColor Yellow
    Push-Location $frontendDir
    npm install
    Pop-Location
}

# ── Lancement des jobs ─────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Démarrage des services..." -ForegroundColor DarkGray

$backendJob = Start-Job -Name "Backend" -ScriptBlock {
    param($root, $python)
    Set-Location $root
    & $python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 2>&1
} -ArgumentList $root, $venvPython

$frontendJob = Start-Job -Name "Frontend" -ScriptBlock {
    param($dir)
    Set-Location $dir
    npm run dev 2>&1
} -ArgumentList $frontendDir

Write-Host "  Backend  → http://localhost:8000      [Ctrl+C pour tout stopper]" -ForegroundColor Cyan
Write-Host "  Frontend → http://localhost:5173" -ForegroundColor Green
Write-Host "  API docs → http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# ── Boucle d'affichage ─────────────────────────────────────────────────────────
try {
    while ($true) {
        foreach ($line in (Receive-Job $backendJob -ErrorAction SilentlyContinue)) {
            Write-Host "[backend]  $line" -ForegroundColor Cyan
        }
        foreach ($line in (Receive-Job $frontendJob -ErrorAction SilentlyContinue)) {
            Write-Host "[frontend] $line" -ForegroundColor Green
        }
        Start-Sleep -Milliseconds 150
    }
}
finally {
    Write-Host ""
    Write-Host "  Arrêt des services..." -ForegroundColor Yellow
    Stop-Job  $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -Force -ErrorAction SilentlyContinue
    Write-Host "  Services arrêtés." -ForegroundColor DarkGray
}

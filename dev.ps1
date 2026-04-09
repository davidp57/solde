# dev.ps1 — Démarre le backend (FastAPI) et le frontend (Vite) en local
# Usage : .\dev.ps1
# Chaque service s'ouvre dans sa propre fenêtre PowerShell.

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# ── Backend ────────────────────────────────────────────────────────────────────
$venvActivate = Join-Path $root ".venv\Scripts\Activate.ps1"
$venvPython   = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "venv introuvable : $venvPython`nLance d'abord : python -m venv .venv && pip install -e .[dev]"
}

$backendCmd = "Set-Location '$root'; & '$venvActivate'; python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", $backendCmd

# ── Frontend ───────────────────────────────────────────────────────────────────
$frontendDir = Join-Path $root "frontend"
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "[frontend] node_modules absent, installation en cours..." -ForegroundColor Yellow
    Push-Location $frontendDir
    npm install
    Pop-Location
}

$frontendCmd = "Set-Location '$frontendDir'; npm run dev"
Start-Process pwsh -ArgumentList "-NoExit", "-Command", $frontendCmd

# ── Résumé ─────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Deux fenêtres PowerShell ont été ouvertes :" -ForegroundColor DarkGray
Write-Host "  Backend  → http://localhost:8000      (fenêtre 1)" -ForegroundColor Green
Write-Host "  Frontend → http://localhost:5173      (fenêtre 2)" -ForegroundColor Green
Write-Host "  API docs → http://localhost:8000/docs (fenêtre 1)" -ForegroundColor Green
Write-Host ""
Write-Host "  Ferme chaque fenêtre ou fais Ctrl+C dedans pour stopper le service." -ForegroundColor DarkGray

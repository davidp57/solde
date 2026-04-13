# dev.ps1 — Démarre le backend (FastAPI) et le frontend (Vite) dans la même session
# Usage : .\dev.ps1   |   Ctrl+C pour tout arrêter

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$scriptShell = Join-Path $PSHOME "pwsh.exe"
if (-not (Test-Path $scriptShell)) {
    $scriptShell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
}

# ── Backend ────────────────────────────────────────────────────────────────────
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "venv introuvable : $venvPython`nLance d'abord : python -m venv .venv && pip install -e .[dev]"
}

# ── Frontend ───────────────────────────────────────────────────────────────────
$frontendDir = Join-Path $root "frontend"
$dataDir = Join-Path $root "data"
$legacyImportsDir = Join-Path $dataDir "imports"
$importSearchDirs = @()
if (Test-Path $legacyImportsDir) {
    $importSearchDirs += $legacyImportsDir
}
$importSearchDirs += $dataDir

function ConvertTo-EncodedCommand {
    param(
        [string]$CommandText
    )

    return [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($CommandText))
}

function Quote-PowerShellLiteral {
    param(
        [string]$Value
    )

    return "'" + $Value.Replace("'", "''") + "'"
}

function New-LogState {
    param(
        [string]$Path,
        [string]$Prefix,
        [string]$Color
    )

    return [pscustomobject]@{
        Path = $Path
        Prefix = $Prefix
        Color = $Color
        LineCount = 0
    }
}

function Write-NewLogLines {
    param(
        [pscustomobject]$LogState
    )

    if (-not (Test-Path $LogState.Path)) {
        return
    }

    $lines = @(Get-Content $LogState.Path -ErrorAction SilentlyContinue)
    if ($lines.Count -le $LogState.LineCount) {
        return
    }

    foreach ($line in ($lines | Select-Object -Skip $LogState.LineCount)) {
        Write-Host "$($LogState.Prefix)$line" -ForegroundColor $LogState.Color
    }

    $LogState.LineCount = $lines.Count
}

function Start-LoggedProcess {
    param(
        [string]$WorkingDirectory,
        [string]$CommandText,
        [string]$LogPath
    )

    $encodedCommand = ConvertTo-EncodedCommand -CommandText $CommandText
    $startProcessArgs = @{
        FilePath = $scriptShell
        WorkingDirectory = $WorkingDirectory
        ArgumentList = @("-NoProfile", "-EncodedCommand", $encodedCommand)
        WindowStyle = "Hidden"
        PassThru = $true
        RedirectStandardOutput = $LogPath
    }

    return Start-Process @startProcessArgs
}

function Stop-LoggedProcess {
    param(
        [System.Diagnostics.Process]$Process
    )

    if ($null -eq $Process) {
        return
    }

    if (Get-Process -Id $Process.Id -ErrorAction SilentlyContinue) {
        & taskkill /PID $Process.Id /T /F *> $null
        Wait-Process -Id $Process.Id -Timeout 2 -ErrorAction SilentlyContinue
    }
}

function Resolve-ImportFilePath {
    param(
        [string[]]$SearchDirs,
        [string[]]$FileNames
    )

    foreach ($searchDir in $SearchDirs) {
        foreach ($fileName in $FileNames) {
            $candidate = Join-Path $searchDir $fileName
            if (Test-Path $candidate) {
                return $candidate
            }
        }
    }

    return Join-Path $SearchDirs[0] $FileNames[0]
}

$gestion2024Path = Resolve-ImportFilePath -SearchDirs $importSearchDirs -FileNames @("Gestion 2024.xlsx")
$gestion2025Path = Resolve-ImportFilePath -SearchDirs $importSearchDirs -FileNames @("Gestion 2025.xlsx")
$comptabilite2024Path = Resolve-ImportFilePath -SearchDirs $importSearchDirs -FileNames @("Comptabilité 2024.xlsx", "Comptabilite 2024.xlsx")
$comptabilite2025Path = Resolve-ImportFilePath -SearchDirs $importSearchDirs -FileNames @("Comptabilité 2025.xlsx", "Comptabilite 2025.xlsx")
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "[frontend] node_modules absent, installation en cours..." -ForegroundColor Yellow
    Push-Location $frontendDir
    npm install
    Pop-Location
}

$logDir = Join-Path $root ".dev-logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$backendLogPath = Join-Path $logDir "backend-$PID.log"
$frontendLogPath = Join-Path $logDir "frontend-$PID.log"
Remove-Item $backendLogPath, $frontendLogPath -Force -ErrorAction SilentlyContinue

$quotedRoot = Quote-PowerShellLiteral -Value $root
$quotedPython = Quote-PowerShellLiteral -Value $venvPython
$quotedFrontendDir = Quote-PowerShellLiteral -Value $frontendDir
$quotedGestion2024Path = Quote-PowerShellLiteral -Value $gestion2024Path
$quotedGestion2025Path = Quote-PowerShellLiteral -Value $gestion2025Path
$quotedComptabilite2024Path = Quote-PowerShellLiteral -Value $comptabilite2024Path
$quotedComptabilite2025Path = Quote-PowerShellLiteral -Value $comptabilite2025Path

$backendCommand = @"
& {
`$ErrorActionPreference = 'Stop'
Set-Location $quotedRoot
`$env:ENABLE_TEST_IMPORT_SHORTCUTS = 'true'
`$env:TEST_IMPORT_GESTION_2024_PATH = $quotedGestion2024Path
`$env:TEST_IMPORT_GESTION_2025_PATH = $quotedGestion2025Path
`$env:TEST_IMPORT_COMPTABILITE_2024_PATH = $quotedComptabilite2024Path
`$env:TEST_IMPORT_COMPTABILITE_2025_PATH = $quotedComptabilite2025Path
Write-Output 'Application des migrations Alembic...'
& $quotedPython -m alembic upgrade head
& $quotedPython -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
} *>&1
"@

$frontendCommand = @"
& {
`$ErrorActionPreference = 'Stop'
Set-Location $quotedFrontendDir
`$env:VITE_DEV_AUTO_LOGIN = 'true'
`$env:VITE_DEV_AUTO_LOGIN_USERNAME = 'admin'
`$env:VITE_DEV_AUTO_LOGIN_PASSWORD = 'admin1234'
npm run dev
} *>&1
"@

$backendLog = New-LogState -Path $backendLogPath -Prefix "[backend]  " -Color "Cyan"
$frontendLog = New-LogState -Path $frontendLogPath -Prefix "[frontend] " -Color "Green"

# ── Lancement des processus ────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Démarrage des services..." -ForegroundColor DarkGray

$backendProcess = Start-LoggedProcess -WorkingDirectory $root -CommandText $backendCommand -LogPath $backendLogPath

Write-Host "  Attente du backend sur http://127.0.0.1:8000..." -ForegroundColor DarkGray
$backendReady = $false
for ($attempt = 0; $attempt -lt 80; $attempt++) {
    Write-NewLogLines -LogState $backendLog

    if ($backendProcess.HasExited) {
        throw "Le backend s'est arrêté avant d'être prêt."
    }

    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/docs" -UseBasicParsing -TimeoutSec 1
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
            $backendReady = $true
            break
        }
    }
    catch {
        # Backend still starting
    }

    Start-Sleep -Milliseconds 250
}

if (-not $backendReady) {
    throw "Le backend n'a pas répondu à temps sur http://127.0.0.1:8000."
}

$frontendProcess = Start-LoggedProcess -WorkingDirectory $frontendDir -CommandText $frontendCommand -LogPath $frontendLogPath

Write-Host "  Backend  → http://localhost:8000      [Ctrl+C pour tout stopper]" -ForegroundColor Cyan
Write-Host "  Frontend → http://localhost:5173" -ForegroundColor Green
Write-Host "  API docs → http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# ── Boucle d'affichage ─────────────────────────────────────────────────────────
try {
    while ($true) {
        Write-NewLogLines -LogState $backendLog
        Write-NewLogLines -LogState $frontendLog

        if ($backendProcess.HasExited) {
            throw "Le backend s'est arrêté de manière inattendue."
        }
        if ($frontendProcess.HasExited) {
            throw "Le frontend s'est arrêté de manière inattendue."
        }

        Start-Sleep -Milliseconds 150
    }
}
finally {
    Write-Host ""
    Write-Host "  Arrêt des services..." -ForegroundColor Yellow
    Stop-LoggedProcess -Process $frontendProcess
    Stop-LoggedProcess -Process $backendProcess
    Write-NewLogLines -LogState $backendLog
    Write-NewLogLines -LogState $frontendLog
    Write-Host "  Services arrêtés." -ForegroundColor DarkGray
}

param([int]$ApiPort = 8000)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$pythonCandidates = @(
    ".\.venv312\Scripts\python.exe",
    ".\.venv\Scripts\python.exe"
)

$python = $pythonCandidates |
    Where-Object { Test-Path $_ } |
    Select-Object -First 1

if (-not $python) {
    throw "Python environment not found. Create .venv312 or .venv and install requirements.txt."
}

$python = (Resolve-Path $python).Path
$env:NETSENTINEL_API = "http://127.0.0.1:$ApiPort"

Write-Host "Using Python: $python"
Write-Host "Starting NetSentinel API..."

$apiProcess = Start-Process -FilePath $python `
    -ArgumentList @("-m", "uvicorn", "app.api.main:app", "--host", "127.0.0.1", "--port", "$ApiPort") `
    -WorkingDirectory $root `
    -PassThru

$healthy = $false

for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1

    if ($apiProcess.HasExited) {
        throw "API process exited unexpectedly. Check the API terminal logs."
    }

    try {
        $response = Invoke-WebRequest -Uri "$($env:NETSENTINEL_API)/health" -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    } catch {}
}

if (-not $healthy) {
    throw "API did not become healthy within 20 seconds."
}

Write-Host "API ready: $($env:NETSENTINEL_API)"
Write-Host "Dashboard: http://localhost:8501"
Write-Host "API docs: $($env:NETSENTINEL_API)/docs"

& $python -m streamlit run app/dashboard/Home.py

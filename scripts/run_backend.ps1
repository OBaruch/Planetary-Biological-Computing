$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
  Write-Host "Creating .venv..."
  py -3.12 -m venv .venv
}

.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn app.main:app --reload --port 8000 --app-dir backend

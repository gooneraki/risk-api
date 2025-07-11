$mode = Read-Host "Start mode? (L)ocal or (D)ocker"

if ($mode -match "^[Dd]") {
    Write-Host "🐳 Starting Docker..."
    docker-compose up --build
} else {
    Write-Host "🚀 Starting Local..."
    . venv\Scripts\Activate.ps1
    uvicorn app.main:app --env-file .env --reload --port 10000
} 
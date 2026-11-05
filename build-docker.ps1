# BULLETPROOF Docker Build Script
# Run this: .\build-docker.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "BULLETPROOF DOCKER BUILD" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify Dockerfile is correct
Write-Host "[1/5] Verifying Dockerfile..." -ForegroundColor Yellow
$dockerfileContent = Get-Content "Dockerfile" -Raw
if ($dockerfileContent -match "libmbedtls12" -or $dockerfileContent -match "libpng16-16") {
    Write-Host "ERROR: Dockerfile still has broken packages!" -ForegroundColor Red
    Write-Host "This should not happen. Dockerfile was just fixed." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dockerfile verified - no broken packages" -ForegroundColor Green
Write-Host ""

# Step 1.5: Verify requirements files don't have known bad/vulnerable versions
Write-Host "[2/5] Verifying requirements files..." -ForegroundColor Yellow
$requirementsApiContent = Get-Content "requirements-api.txt" -Raw
if ($requirementsApiContent -match "starlette==0\.41\.4") {
    Write-Host "ERROR: requirements-api.txt has non-existent starlette version!" -ForegroundColor Red
    Write-Host "starlette==0.41.4 does not exist. Use 0.49.1 instead." -ForegroundColor Red
    exit 1
}
if ($requirementsApiContent -match "starlette==0\.41\.3") {
    Write-Host "ERROR: requirements-api.txt has vulnerable starlette version!" -ForegroundColor Red
    Write-Host "starlette==0.41.3 has CVE-2025-62727 (HIGH). Upgrade to 0.49.1" -ForegroundColor Red
    exit 1
}
if ($requirementsApiContent -match "pip==24\.0") {
    Write-Host "WARNING: Dockerfile uses pip 24.0 with CVE-2025-8869 (MEDIUM)" -ForegroundColor Yellow
    Write-Host "Recommend upgrading to pip 25.3 in Dockerfile" -ForegroundColor Yellow
}
Write-Host "✓ Requirements files verified - no known bad versions" -ForegroundColor Green
Write-Host ""

# Step 2: Clean Docker cache
Write-Host "[3/5] Cleaning Docker cache..." -ForegroundColor Yellow
docker builder prune -f | Out-Null
Write-Host "✓ Cache cleaned" -ForegroundColor Green
Write-Host ""

# Step 3: Build image
Write-Host "[4/5] Building Docker image..." -ForegroundColor Yellow
Write-Host "This will take 5-10 minutes..." -ForegroundColor Gray
Write-Host ""

docker build --no-cache --pull -t maaps-api:latest .

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "BUILD FAILED!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible causes:" -ForegroundColor Yellow
    Write-Host "1. Internet connection issues" -ForegroundColor Yellow
    Write-Host "2. Docker daemon not running" -ForegroundColor Yellow
    Write-Host "3. Missing requirements.txt or requirements-api.txt" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "✓ Build SUCCESSFUL!" -ForegroundColor Green
Write-Host ""

# Step 4: Verify image
Write-Host "[5/5] Verifying image..." -ForegroundColor Yellow
$imageExists = docker images maaps-api:latest --format "{{.Repository}}"
if ($imageExists -eq "maaps-api") {
    $imageSize = docker images maaps-api:latest --format "{{.Size}}"
    Write-Host "✓ Image created: maaps-api:latest ($imageSize)" -ForegroundColor Green
} else {
    Write-Host "ERROR: Image was not created!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Scan for vulnerabilities if available
Write-Host "Scanning for vulnerabilities..." -ForegroundColor Yellow
try {
    docker scout cves maaps-api:latest 2>&1 | Out-Null
    Write-Host "Running Docker Scout scan..." -ForegroundColor Gray
    docker scout cves maaps-api:latest
} catch {
    Write-Host "Docker Scout not available (install: https://docs.docker.com/scout/install/)" -ForegroundColor Gray
}
Write-Host ""

# Success
Write-Host "================================" -ForegroundColor Green
Write-Host "BUILD COMPLETE!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Test: docker run -p 8000:8000 --env-file .env maaps-api:latest" -ForegroundColor White
Write-Host "2. Health check: curl http://localhost:8000/health" -ForegroundColor White
Write-Host "3. API docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""

# Secure Docker Build and Deployment Script (PowerShell)
# Builds MAAPS API with security hardening and vulnerability reduction

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MAAPS API - Secure Docker Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Blue

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker is not installed" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Docker found" -ForegroundColor Green
Write-Host ""

# Backup old Dockerfile if exists
if ((Test-Path "Dockerfile") -and (-not (Test-Path "Dockerfile.backup"))) {
    Write-Host "Backing up original Dockerfile..." -ForegroundColor Blue
    Copy-Item "Dockerfile" "Dockerfile.backup"
    Write-Host "✓ Backup created: Dockerfile.backup" -ForegroundColor Green
}

# Use fixed Dockerfile
if (Test-Path "Dockerfile.fixed") {
    Write-Host "Using security-hardened Dockerfile..." -ForegroundColor Blue
    Copy-Item "Dockerfile.fixed" "Dockerfile" -Force
    Write-Host "✓ Dockerfile updated" -ForegroundColor Green
}
Write-Host ""

# Check .dockerignore
if (-not (Test-Path ".dockerignore")) {
    Write-Host "Warning: .dockerignore not found" -ForegroundColor Yellow
    Write-Host "Creating .dockerignore to exclude secrets..." -ForegroundColor Yellow

    @"
.env
.env.*
*.db
__pycache__
.git
node_modules/
.vscode/
.idea/
*.log
"@ | Set-Content ".dockerignore"

    Write-Host "✓ .dockerignore created" -ForegroundColor Green
}
Write-Host ""

# Check environment file
if (-not (Test-Path ".env")) {
    Write-Host "Error: .env file not found" -ForegroundColor Red
    Write-Host "Please create .env file with required variables:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "JWT_SECRET=your-secret-here"
    Write-Host "DB_PASSWORD=your-db-password"
    Write-Host "REDIS_PASSWORD=your-redis-password"
    Write-Host "GRAFANA_PASSWORD=your-grafana-password"
    Write-Host "ALLOWED_ORIGINS=https://yourdomain.com"
    Write-Host ""
    exit 1
}

# Build image
Write-Host "Building Docker image..." -ForegroundColor Blue
Write-Host "This may take 5-10 minutes..." -ForegroundColor Yellow
Write-Host ""

docker build `
    --no-cache `
    --pull `
    -t maaps-api:latest `
    -f Dockerfile `
    .

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Build successful!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ Build failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Get image size
$imageInfo = docker images maaps-api:latest --format "{{.Size}}"
Write-Host "Image size: $imageInfo" -ForegroundColor Green
Write-Host ""

# Scan for vulnerabilities if Docker Scout is available
try {
    docker scout version 2>&1 | Out-Null
    Write-Host "Scanning for vulnerabilities..." -ForegroundColor Blue
    docker scout cves maaps-api:latest
    Write-Host ""

    Write-Host "Getting recommendations..." -ForegroundColor Blue
    docker scout recommendations maaps-api:latest
    Write-Host ""
} catch {
    Write-Host "Docker Scout not available, skipping vulnerability scan" -ForegroundColor Yellow
    Write-Host "To install: https://docs.docker.com/scout/install/" -ForegroundColor Yellow
    Write-Host ""
}

# Ask if user wants to run
Write-Host ""
$run = Read-Host "Do you want to run the container now? (y/n)"

if ($run -eq "y" -or $run -eq "Y") {
    Write-Host "Starting container..." -ForegroundColor Blue

    docker run -d `
        --name maaps-api `
        -p 8000:8000 `
        --env-file .env `
        -v "${PWD}/data:/app/data" `
        -v "${PWD}/logs:/app/logs" `
        maaps-api:latest

    Write-Host ""
    Write-Host "✓ Container started" -ForegroundColor Green
    Write-Host ""

    $containerId = docker ps -aqf "name=maaps-api"
    Write-Host "Container ID: $containerId"
    Write-Host ""
    Write-Host "View logs: docker logs -f maaps-api"
    Write-Host "Stop: docker stop maaps-api"
    Write-Host "Remove: docker rm maaps-api"
    Write-Host ""

    # Wait for health check
    Write-Host "Waiting for health check..." -ForegroundColor Blue
    Start-Sleep -Seconds 5

    # Test health endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Health check passed" -ForegroundColor Green
            Write-Host ""
            Write-Host "API available at: http://localhost:8000"
            Write-Host "API docs: http://localhost:8000/docs"
        }
    } catch {
        Write-Host "Health check pending... check logs" -ForegroundColor Yellow
        Write-Host "docker logs maaps-api"
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Run: docker run -p 8000:8000 --env-file .env maaps-api:latest"
Write-Host "2. Test: curl http://localhost:8000/health"
Write-Host "3. View docs: http://localhost:8000/docs"
Write-Host ""
Write-Host "For production deployment:"
Write-Host "docker-compose -f docker-compose.secure.yml up -d"
Write-Host ""

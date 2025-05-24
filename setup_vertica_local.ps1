# 🐘 Vertica Community Edition Setup Script for Windows
# This script sets up Vertica CE using Docker Desktop

Write-Host "🐘 Setting up Vertica Community Edition locally..." -ForegroundColor Green
Write-Host "=" * 60

# Check if Docker is installed and running
Write-Host "🔍 Checking Docker Desktop..." -ForegroundColor Yellow
try {
    docker --version
    docker info | Out-Null
    Write-Host "✅ Docker Desktop is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Desktop not found or not running!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Write-Host "Then restart this script." -ForegroundColor Yellow
    exit 1
}

# Stop and remove existing Vertica container if it exists
Write-Host "🧹 Cleaning up any existing Vertica containers..." -ForegroundColor Yellow
docker stop vertica-ce 2>$null
docker rm vertica-ce 2>$null
docker volume rm vertica-data 2>$null

# Pull Vertica Community Edition
Write-Host "📥 Pulling Vertica Community Edition container..." -ForegroundColor Yellow
Write-Host "This may take a few minutes for the first time..." -ForegroundColor Cyan
docker pull opentext/vertica-ce:latest

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to pull Vertica image!" -ForegroundColor Red
    exit 1
}

# Run Vertica container
Write-Host "🚀 Starting Vertica Community Edition..." -ForegroundColor Yellow
$containerCmd = @"
docker run -d \
  --name vertica-ce \
  -p 5433:5433 \
  -p 5444:5444 \
  -e VERTICA_DB_NAME=testdb \
  -e VERTICA_DB_PASSWORD=password123 \
  --memory=4g \
  --memory-swap=8g \
  -v vertica-data:/home/dbadmin/docker \
  opentext/vertica-ce:latest
"@

Invoke-Expression $containerCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start Vertica container!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Vertica container started successfully!" -ForegroundColor Green

# Wait for Vertica to initialize
Write-Host "⏳ Waiting for Vertica to initialize (this may take 2-5 minutes)..." -ForegroundColor Yellow
$attempts = 0
$maxAttempts = 30

do {
    Start-Sleep 10
    $attempts++
    Write-Host "   Attempt $attempts/$maxAttempts - Checking Vertica status..." -ForegroundColor Cyan
    
    $logs = docker logs vertica-ce 2>&1
    if ($logs -match "Database testdb created successfully" -or $logs -match "Vertica is now running") {
        Write-Host "✅ Vertica is ready!" -ForegroundColor Green
        break
    }
    
    if ($attempts -ge $maxAttempts) {
        Write-Host "⚠️  Vertica is taking longer than expected to start." -ForegroundColor Yellow
        Write-Host "   You can check logs with: docker logs vertica-ce" -ForegroundColor Cyan
        break
    }
} while ($true)

# Display connection information
Write-Host ""
Write-Host "🎉 VERTICA SETUP COMPLETE!" -ForegroundColor Green
Write-Host "=" * 60
Write-Host "📊 Connection Details:" -ForegroundColor Cyan
Write-Host "   Host: localhost" -ForegroundColor White
Write-Host "   Port: 5433" -ForegroundColor White
Write-Host "   Database: testdb" -ForegroundColor White
Write-Host "   Username: dbadmin" -ForegroundColor White
Write-Host "   Password: password123" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Useful Commands:" -ForegroundColor Cyan
Write-Host "   Check status:    docker ps" -ForegroundColor White
Write-Host "   View logs:       docker logs vertica-ce" -ForegroundColor White
Write-Host "   Connect to DB:   docker exec -it vertica-ce vsql -U dbadmin -d testdb" -ForegroundColor White
Write-Host "   Stop Vertica:    docker stop vertica-ce" -ForegroundColor White
Write-Host "   Start Vertica:   docker start vertica-ce" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Web Access:" -ForegroundColor Cyan
Write-Host "   Management Console: http://localhost:5444" -ForegroundColor White
Write-Host ""
Write-Host "Next: Run 'python test_vertica_connection.py' to test the connection!" -ForegroundColor Green 
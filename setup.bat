@echo off
REM Setup script for local development (Windows)

echo.
echo 🚀 DateGen Setup
echo.

REM Check prerequisites
echo Checking prerequisites...

where docker >nul 2>nul
if errorlevel 1 (
    echo ❌ Docker is not installed
    exit /b 1
)

where docker-compose >nul 2>nul
if errorlevel 1 (
    echo ❌ Docker Compose is not installed
    exit /b 1
)

echo ✅ Docker found
echo ✅ Docker Compose found
echo.

REM Setup environment
echo Setting up environment...
if not exist .env (
    copy .env.template .env
    echo ✅ Created .env from template
    echo ⚠️  Please edit .env with your API keys before starting!
) else (
    echo ✅ .env already exists
)

echo.

REM Start services
echo Starting Docker services...
docker-compose up -d

echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak

echo.
echo ✅ Setup complete!
echo.
echo 📍 Access the app:
echo    Frontend: http://localhost:5173
echo    Backend:  http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
echo 🛑 To stop: docker-compose down
echo 📊 To view logs: docker-compose logs -f

@echo off
REM Local development setup script for Windows

echo Starting local development environment...

REM Activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
)

REM Start services with docker-compose
echo Starting Docker services...
docker-compose -f docker\docker-compose.yml up -d

REM Wait for services to be ready
echo Waiting for services to be ready...
timeout /t 10 /nobreak

REM Initialize database
echo Initializing database...
python -c "from db.connection import init_db; init_db()"

echo Setup complete!
echo.
echo To start the API: uvicorn api.app.main:app --reload
echo To start the worker: python -m worker_orchestration.consumer
echo To start the frontend: cd web ^&^& npm run dev


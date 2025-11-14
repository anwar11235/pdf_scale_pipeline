#!/bin/bash
# Local development setup script

echo "Starting local development environment..."

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Start services with docker-compose
echo "Starting Docker services..."
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Initialize database
echo "Initializing database..."
python -c "from db.connection import init_db; init_db()"

echo "Setup complete!"
echo ""
echo "To start the API: uvicorn api.app.main:app --reload"
echo "To start the worker: python -m worker_orchestration.consumer"
echo "To start the frontend: cd web && npm run dev"


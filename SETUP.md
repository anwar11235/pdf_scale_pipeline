# Setup Guide

This guide will help you set up the Document Processing Pipeline from scratch.

## Prerequisites

Before starting, ensure you have:

- **Python 3.10+** installed
- **Node.js 18+** and npm installed
- **Docker** and **Docker Compose** installed
- **Git** installed

## Step-by-Step Setup

### 1. Clone and Navigate

```bash
cd pdf-pipe
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 3. Set Up Frontend

```bash
cd web
npm install
cd ..
```

### 4. Configure Environment

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` with your configuration (defaults should work for local development).

### 5. Start Infrastructure Services

```bash
# Start PostgreSQL, MinIO, Redis, Elasticsearch
docker-compose -f docker/docker-compose.yml up -d
```

Wait a few seconds for services to start, then verify:

```bash
# Check services are running
docker-compose -f docker/docker-compose.yml ps
```

### 6. Initialize Database

```bash
# Option 1: Using Python
python -c "from db.connection import init_db; init_db()"

# Option 2: Using psql directly
psql -h localhost -U user -d docdb -f db/models.sql
# Password: pass
```

### 7. Start Application Services

You'll need **three terminals**:

#### Terminal 1: API Server
```bash
# Activate venv if not already
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start API
uvicorn api.app.main:app --reload --port 8000
```

#### Terminal 2: Worker
```bash
# Activate venv if not already
source venv/bin/activate

# Start worker
python -m worker_orchestration.consumer
```

#### Terminal 3: Frontend
```bash
cd web
npm run dev
```

### 8. Verify Installation

1. **API**: Visit http://localhost:8000/docs - You should see the FastAPI documentation
2. **Frontend**: Visit http://localhost:3000 - You should see the upload page
3. **MinIO Console**: Visit http://localhost:9001 (minioadmin/minioadmin)
4. **Elasticsearch**: Visit http://localhost:9200 - Should return cluster info

## Testing the Setup

### Upload a Test PDF

1. Go to http://localhost:3000
2. Click "Upload" and select a PDF file
3. Watch the status page for processing progress
4. Once complete, view the extracted text and fields

### Check Logs

- **API logs**: Check Terminal 1
- **Worker logs**: Check Terminal 2
- **Docker logs**: `docker-compose -f docker/docker-compose.yml logs -f`

## Troubleshooting

### Port Already in Use

If a port is already in use:

```bash
# Find process using port
# Windows:
netstat -ano | findstr :8000
# Linux/Mac:
lsof -i :8000

# Kill process or change port in docker-compose.yml
```

### Database Connection Error

1. Verify PostgreSQL is running: `docker-compose -f docker/docker-compose.yml ps`
2. Check connection string in `.env`
3. Try restarting: `docker-compose -f docker/docker-compose.yml restart postgres`

### Tesseract Not Found

Install Tesseract:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# macOS
brew install tesseract

# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### Module Import Errors

Ensure you're in the project root and virtual environment is activated:

```bash
# Verify Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install -r requirements.txt
```

### MinIO Bucket Not Created

The S3 client should auto-create the bucket. If not:

1. Go to http://localhost:9001
2. Login with minioadmin/minioadmin
3. Create bucket named "documents"

## Next Steps

- Read the [README.md](README.md) for usage instructions
- Check [architecture.md](architecture.md) for system design
- Review [backend.md](backend.md) and [frontend.md](frontend.md) for implementation details

## Production Deployment

For production deployment:

1. Use managed services (RDS, ElastiCache, etc.) instead of Docker containers
2. Set up proper authentication (JWT/Supabase)
3. Configure SSL/TLS
4. Set up monitoring and alerting
5. Use environment-specific configuration
6. Set up CI/CD pipeline

See the README for more details.


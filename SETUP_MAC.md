# MacBook Setup Guide

This guide is specifically for setting up the Document Processing Pipeline on macOS.

## Prerequisites for Mac

### 1. Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Required Tools

```bash
# Install Python 3.10+ (if not already installed)
brew install python@3.11

# Install Node.js 18+
brew install node@18

# Install Docker Desktop for Mac
# Download from: https://www.docker.com/products/docker-desktop
# Or use Homebrew:
brew install --cask docker

# Install Tesseract OCR
brew install tesseract tesseract-lang

# Install Git (usually pre-installed, but just in case)
brew install git
```

### 3. Verify Installations

```bash
python3 --version  # Should be 3.10+
node --version      # Should be 18+
docker --version
tesseract --version
```

## Step-by-Step Setup

### 1. Navigate to Project Directory

```bash
cd pdf-pipe
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

**Note:** If you get permission errors, you might need to use `python3` instead of `python`.

### 3. Set Up Frontend

```bash
cd web
npm install
cd ..
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env if needed (defaults work for local development)
# You can use nano, vim, or any text editor:
# nano .env
```

### 5. Start Docker Desktop

**Important:** Make sure Docker Desktop is running before proceeding.

1. Open Docker Desktop application
2. Wait for it to fully start (whale icon in menu bar should be steady)
3. Verify it's running: `docker ps` should not give an error

### 6. Start Infrastructure Services

```bash
# Start PostgreSQL, MinIO, Redis, Elasticsearch
docker-compose -f docker/docker-compose.yml up -d

# Wait a few seconds, then verify services are running
docker-compose -f docker/docker-compose.yml ps
```

You should see all services with "Up" status.

### 7. Initialize Database

```bash
# Make sure venv is activated
source venv/bin/activate

# Initialize database using Python
python -c "from db.connection import init_db; init_db()"
```

### 8. Start Application Services

You'll need **three terminal windows/tabs**:

#### Terminal 1: API Server
```bash
# Navigate to project root
cd pdf-pipe

# Activate virtual environment
source venv/bin/activate

# Start API server
uvicorn api.app.main:app --reload --port 8000
```

#### Terminal 2: Worker
```bash
# Navigate to project root
cd pdf-pipe

# Activate virtual environment
source venv/bin/activate

# Start worker
python -m worker_orchestration.consumer
```

#### Terminal 3: Frontend
```bash
# Navigate to web directory
cd pdf-pipe/web

# Start Next.js dev server
npm run dev
```

### 9. Verify Everything is Working

1. **API**: Open http://localhost:8000/docs in your browser
   - You should see the FastAPI interactive documentation

2. **Frontend**: Open http://localhost:3000
   - You should see the upload page

3. **MinIO Console**: Open http://localhost:9001
   - Login with: `minioadmin` / `minioadmin`

4. **Elasticsearch**: Test in terminal
   ```bash
   curl http://localhost:9200
   ```

## Mac-Specific Tips

### Using the Helper Script

You can use the provided setup script:

```bash
# Make it executable
chmod +x run_local.sh

# Run it
./run_local.sh
```

### Python Command Issues

If `python` doesn't work, use `python3`:

```bash
# Instead of: python -m venv venv
python3 -m venv venv

# Instead of: python -c "..."
python3 -c "..."
```

### Port Conflicts

If you get "port already in use" errors:

```bash
# Find what's using the port
lsof -i :8000  # For API
lsof -i :3000  # For frontend
lsof -i :5432  # For PostgreSQL

# Kill the process (replace PID with actual process ID)
kill -9 <PID>
```

### Docker Memory Issues

If Docker containers are slow or crashing:

1. Open Docker Desktop
2. Go to Settings → Resources
3. Increase Memory allocation (recommended: 4GB+)
4. Apply & Restart

### Tesseract Path Issues

If Tesseract isn't found:

```bash
# Verify installation
which tesseract

# If not found, add to PATH (add to ~/.zshrc or ~/.bash_profile)
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Permission Issues

If you get permission errors:

```bash
# Fix file permissions
chmod +x run_local.sh

# For npm packages
sudo chown -R $(whoami) ~/.npm
```

## Troubleshooting

### "Command not found: docker-compose"

On newer Docker Desktop versions, use `docker compose` (without hyphen):

```bash
# Instead of: docker-compose
docker compose -f docker/docker-compose.yml up -d
```

### Python Virtual Environment Issues

```bash
# If venv activation doesn't work
deactivate  # Exit any existing venv
rm -rf venv  # Remove old venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Node/npm Issues

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
cd web
rm -rf node_modules package-lock.json
npm install
```

### Docker Services Not Starting

```bash
# Check Docker is running
docker ps

# View logs
docker-compose -f docker/docker-compose.yml logs

# Restart services
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml up -d
```

## Quick Test

Once everything is running:

1. Go to http://localhost:3000
2. Upload a test PDF file
3. Watch the status page for processing
4. View extracted results

## Stopping Services

To stop all services:

```bash
# Stop Docker services
docker-compose -f docker/docker-compose.yml down

# Stop API/Worker: Press Ctrl+C in their terminals
# Stop Frontend: Press Ctrl+C in its terminal
```

## Next Steps

- Read [README.md](README.md) for detailed usage
- Check [SETUP.md](SETUP.md) for general setup info
- Review [architecture.md](architecture.md) for system design

## Need Help?

Common Mac-specific issues:
- **M1/M2 Macs**: All dependencies should work natively now
- **Intel Macs**: Everything should work as-is
- **Docker Desktop**: Make sure it's the latest version for best compatibility


# Document Processing Pipeline

A large-scale document processing pipeline that ingests PDFs, distinguishes native-text vs scanned-image PDFs, performs OCR, layout detection, table extraction, and routes low-confidence items to cloud OCR or human review.

## Features

- **PDF Classification**: Automatically detects native text vs scanned PDFs
- **Image Preprocessing**: Deskew, denoise, resize to 300 DPI, binarize
- **Layout Detection**: Uses LayoutParser/PubLayNet to detect paragraphs, headers, tables, forms
- **OCR**: Open-source baseline (OCRmyPDF/Tesseract) with optional neural OCR (TrOCR)
- **Table Extraction**: Extracts tables from both native and scanned PDFs
- **Field Extraction**: NER-based extraction using spaCy and regex patterns
- **Cloud OCR Fallback**: Routes low-confidence items to Google Document AI, AWS Textract, or Azure
- **Human-in-the-Loop**: Review interface for flagged documents
- **Search & Indexing**: Stores results in Postgres and indexes to Elasticsearch

## Architecture

```
┌─────────┐     ┌──────────┐     ┌─────────┐
│  API    │────▶│  Queue   │────▶│ Worker  │
│(FastAPI)│     │ (Redis)  │     │(Orchestrator)
└─────────┘     └──────────┘     └─────────┘
     │                                │
     ▼                                ▼
┌─────────┐                     ┌─────────┐
│   S3    │                     │ Postgres│
│ (MinIO) │                     │   DB    │
└─────────┘                     └─────────┘
                                        │
                                        ▼
                                 ┌─────────────┐
                                 │Elasticsearch│
                                 └─────────────┘
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis
- Tesseract OCR

## Quick Start

### 1. Set up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Set up Frontend

```bash
cd web
npm install
```

### 3. Start Services with Docker Compose

```bash
docker-compose -f docker/docker-compose.yml up -d
```

This will start:
- PostgreSQL (port 5432)
- MinIO (S3-compatible storage, ports 9000, 9001)
- Redis (port 6379)
- Elasticsearch (port 9200)

### 4. Initialize Database

```bash
# Connect to PostgreSQL and run schema
psql -h localhost -U user -d docdb -f db/models.sql

# Or use Python to initialize
python -c "from db.connection import init_db; init_db()"
```

### 5. Configure Environment Variables

Create a `.env` file:

```bash
# Database
POSTGRES_URL=postgresql://user:pass@localhost:5432/docdb

# Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=documents

# Queue
REDIS_URL=redis://localhost:6379

# Search
ELASTIC_URL=http://localhost:9200

# OCR
OCR_CONF_THRESHOLD=0.85

# Cloud OCR (optional)
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_DOCAI_PROCESSOR_ID=your-processor-id
CLOUD_OCR_AWS_ACCESS_KEY=your-access-key
CLOUD_OCR_AWS_SECRET=your-secret-key
```

### 6. Start Backend API

```bash
# In one terminal
uvicorn api.app.main:app --reload --port 8000
```

### 7. Start Worker

```bash
# In another terminal
python -m worker_orchestration.consumer
```

### 8. Start Frontend

```bash
# In another terminal
cd web
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Usage

### Upload a Document

1. Navigate to http://localhost:3000
2. Click "Upload" and select a PDF file
3. Wait for processing to complete
4. View results on the status page

### Review Flagged Documents

1. Navigate to "Flagged" in the sidebar
2. Click on a flagged document
3. Review extracted fields and make corrections
4. Submit your decision (Approve, Reject, etc.)

## API Endpoints

### `POST /api/upload`
Upload a PDF document for processing.

**Request:**
- `file`: PDF file (multipart/form-data)
- `source`: Optional source identifier
- `applicant_id`: Optional applicant ID
- `doc_type`: Optional document type

**Response:**
```json
{
  "doc_id": "uuid",
  "status_url": "/api/status/{doc_id}",
  "result_url": "/api/result/{doc_id}",
  "presigned_url": "optional-presigned-url"
}
```

### `GET /api/status/{doc_id}`
Get processing status for a document.

### `GET /api/result/{doc_id}`
Get processing results including extracted text, fields, and tables.

### `POST /api/retry/{doc_id}`
Retry processing a document.

### `GET /api/flagged`
Get list of documents flagged for human review.

### `POST /api/human_review/{doc_id}`
Submit human review decision for a flagged document.

## Testing

### Unit Tests

```bash
python -m pytest tests/unit/
```

### Integration Tests

```bash
python -m pytest tests/integration/
```

### Benchmark

```bash
# Place sample PDFs in tests/samples/
python tests/benchmark.py tests/samples/
```

This will generate a CSV report with processing metrics.

## Project Structure

```
pdf-pipe/
├── api/                 # FastAPI application
│   └── app/
│       ├── main.py      # FastAPI app
│       └── routers/     # API routes
├── workers/             # Worker orchestration
├── classifier/          # Text layer detection
├── preprocess/          # Image preprocessing
├── layout/              # Layout detection
├── ocr/                 # OCR workers and adapters
├── extractor/           # Table extraction
├── postprocess/         # NER and field extraction
├── storage/             # S3 client
├── db/                  # Database models
├── web/                 # Next.js frontend
├── tests/               # Test suites
├── docker/              # Docker configuration
└── requirements.txt     # Python dependencies
```

## Development

### Running Locally (without Docker)

1. Install PostgreSQL, Redis, and MinIO locally
2. Update environment variables to point to local services
3. Run API and worker as described above

### Docker Development

```bash
# Build and start all services
docker-compose -f docker/docker-compose.yml up --build

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down
```

## Monitoring

### Metrics

Prometheus metrics are available at `/metrics` endpoint.

Key metrics:
- `docs_processed_total`: Total documents processed
- `ocr_failures_total`: OCR failures
- `avg_processing_seconds`: Average processing time
- `percent_flagged_for_review`: Percentage flagged

### Logs

Logs are output to stdout/stderr. In production, configure logging to your preferred service.

## Production Deployment

### Kubernetes

See `infra/` directory for sample Kubernetes manifests (to be added).

### Environment Variables

Ensure all required environment variables are set in production:
- Database credentials
- S3/object storage credentials
- Cloud OCR API keys (if using)
- Redis connection string
- Elasticsearch URL

## Troubleshooting

### Tesseract not found

Install Tesseract:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### LayoutParser model download

On first run, LayoutParser will download models. Ensure you have internet connectivity and sufficient disk space.

### Database connection errors

Verify:
- PostgreSQL is running
- Connection string is correct
- Database exists
- User has proper permissions

## License

[Your License Here]

## Contributing

[Contributing Guidelines]


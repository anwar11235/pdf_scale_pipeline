
---

# `backend.md`

```markdown
# Backend: Implementation Details and Tasks

## Purpose
Detailed backend specification for Cursor to implement the server-side of the document pipeline:
- APIs for upload/status/results
- Worker orchestration (classifier → preprocess → layout → OCR → extract → postprocess → index)
- Storage (S3-compatible) + Postgres metadata
- Cloud OCR adapters + HITL routes
- Logging, metrics, and tests

## Tech stack (recommended)
- Language: Python 3.10+
- API: FastAPI
- Workers: RQ / Celery or custom asyncio queue worker (Redis/Redis Stream)
- Storage: MinIO (S3-compatible) locally; AWS S3/GCS in prod
- DB: Postgres (Supabase for auth + hosted Postgres optional)
- Search: OpenSearch / Elasticsearch
- OCR: OCRmyPDF + Tesseract for baseline; TrOCR (transformer) optionally for hard cases
- Layout: LayoutParser (PyTorch) with PubLayNet model
- Table extraction: Camelot / PDFPlumber
- NER / Postprocess: spaCy + custom regexes; LLM call optional for fuzzy extraction
- Containerization: Docker, docker-compose; k8s manifests for production
- Logging/metrics: Prometheus + Grafana or simple Prometheus-compatible metrics endpoint

## Backend directory (detailed)
api/
├── app/
│ ├── main.py # FastAPI app + route registration
│ ├── deps.py # dependency injection
│ ├── routers/
│ │ ├── upload.py
│ │ ├── status.py
│ │ ├── result.py
│ │ └── admin.py
│ ├── models/ # pydantic request/response schemas
│ └── services/ # thin wrappers calling worker orchestrator
workers/
├── orchestrator.py # main orchestration logic
├── steps/
│ ├── detect_text_layer.py
│ ├── preprocessor.py
│ ├── layout.py
│ ├── ocr_oss.py
│ ├── ocr_trocr.py
│ ├── cloud_adapters.py
│ └── postprocess.py
storage/
├── s3_client.py # wrapper around boto3
db/
├── models.sql # schema migrations / creation
tests/
├── unit/
└── integration/
docker/
├── Dockerfile.api
├── Dockerfile.worker
└── docker-compose.yml


## API: Endpoint details
### `POST /upload`
- Accepts multipart file(s), metadata (source, applicant_id, doc_type)
- Behavior:
  - Store original PDF in S3 under `raw/{doc_id}.pdf`
  - Insert metadata row in Postgres (status=queued)
  - Enqueue processing task with doc_id
  - Return `{doc_id, status_url, result_url}`

### `GET /status/{doc_id}`
- Returns processing status, current step, timestamps, and percentage (based on steps completed)

### `GET /result/{doc_id}`
- Returns:
  - Extracted plain text per page
  - Per-page bounding boxes and OCR confidences
  - Extracted structured fields (JSON)
  - Table data (CSV/JSON)
  - Processing metadata + logs

### `POST /retry/{doc_id}`
- Accepts body `{step?: string}` to re-run from a particular step (idempotent)

### `GET /flagged`
- Returns list of documents flagged for human review

### `POST /human_review/{doc_id}`
- Accepts reviewer decisions and comments; updates database and triggers follow-up actions

## Worker orchestration (flow & pseudocode)
1. `consumer` pulls doc_id
2. `detect_text_layer`:
   - If native text: extract via pdfminer/pdfplumber and go to postprocess/extractor directly
3. `if scanned`:
   - `preprocess` → `layout` → produce bboxes
   - For each bbox block:
     - If 'table' → route to `table_extractor`
     - Else → OCR region via `ocr_oss.py` (OCRmyPDF/Tesseract)
4. `postprocess`:
   - Clean text, apply NER/field extraction
   - Assign confidence score per field
   - If confidence < threshold and document value high → `cloud_adapter` call
   - If still low → mark flagged for human review
5. `store` results to Postgres and index to OpenSearch
6. `notify` via webhook / pubsub if human review required

### Idempotency
- Each step writes a "checkpoint" row in Postgres (doc_id, step, status, timestamp). Re-run should be safe.

## Cloud OCR adapters (contracts)
- Each adapter must implement `analyze_document(bucket, key) -> {pages: [{text, bboxes, confidences}], meta: {}}`
- Provide adapters for:
  - Google Document AI
  - AWS Textract
  - Azure Form Recognizer
- Adapters must respect rate limits and implement exponential backoff

## Data model (Postgres tables sketch)
- `documents` (id, owner_id, filename, s3_key, status, created_at, updated_at)
- `pages` (id, document_id, page_no, s3_image_key, ocr_text, ocr_confidence)
- `fields` (id, document_id, field_name, field_value, confidence, bbox_json)
- `tables` (id, document_id, page_no, csv_s3_key, extracted_rows_json)
- `audit_logs` (id, document_id, action, user_id, details, created_at)
- `reprocess_tasks` (id, document_id, step, attempts, last_attempted_at)

## Postprocess / NER guidance
- Use spaCy (with `en_core_web_trf` if GPU available) for robust entity extraction.
- Add domain-specific custom rules:
  - Income: regex for `\$?\d{1,3}(?:,\d{3})*(?:\.\d+)?`
  - Dates: ISO normalization
  - Bank account/IBAN masks (redact sensitive)
- Provide an LLM-parsing fallback for ambiguous extraction (record prompt + response in `audit_logs`)

## Human-in-the-loop (HITL)
- Minimal endpoints:
  - `GET /flagged` → lists flagged docs with prefilled form (fields + current confidence)
  - `POST /human_review/{doc_id}` → accept corrections
- Worker must accept corrections and retrain/tune heuristics (save corrections as training data)

## Security
- All API routes secured with JWT (Supabase or custom)
- File uploads streamed directly to S3 (pre-signed URL generation recommended)
- Validate file types & size
- Sanitize all content written to DB
- Audit trail must record who accessed or changed any decision

## Testing requirements (deliverables)
- Unit tests for:
  - `detect_text_layer` logic (native vs scanned)
  - `preprocess` transformations (assert image DPI, size)
  - `ocr_oss` wrapper (mocked)
  - `table_extractor` on three synthetic table PDFs
- Integration test:
  - Full run on sample PDF (native + scanned) using `docker-compose` stack
- Provide `tests/benchmark.py` script to run on a folder of PDFs producing a CSV report

## Docker & local dev
- Provide:
  - `docker/Dockerfile.api` → FastAPI + uvicorn
  - `docker/Dockerfile.worker` → worker image with Tesseract installed
  - `docker/docker-compose.yml` → Postgres, MinIO, Redis, ElasticSearch, api, worker
- Example compose command:
  - `docker-compose -f docker/docker-compose.yml up --build`
- Provide README with env var examples, sample `sample_env.sh`

## Monitoring & Observability
- Expose `/metrics` endpoint with Prometheus counters:
  - `docs_processed_total`
  - `ocr_failures_total`
  - `avg_processing_seconds`
  - `percent_flagged_for_review`
- Provide sample Grafana dashboard JSON (basic)

## Acceptance criteria (backend)
- Cursor must provide a working FastAPI service with the endpoints above and a worker that can process sample PDFs in `tests/samples/`.
- Cloud adapters should be included but can be in "mock" mode if keys not supplied.
- All code must have tests and a benchmark script.
- DB schema & sample migration script must be present.

---
# End of backend.md

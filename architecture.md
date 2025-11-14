# Architecture: OCR + Layout + Hybrid Cloud Fallback Pipeline

## Purpose
Provide Cursor with a clear architecture and project layout to implement a large-scale document processing pipeline that:
- Ingests hundreds of thousands of PDFs
- Distinguishes native-text vs scanned-image PDFs
- Preprocesses images (deskew/denoise/DPI)
- Performs layout detection, OCR (OSS primary), table & form extraction
- Routes low-confidence items to cloud OCR or human review
- Stores results and supports search and an audit trail

## High-level architecture (text):
1. **Ingest**  
   - Object store (S3-compatible) holds original PDFs.  
   - Message broker (Kafka/SQS) enqueues document processing tasks.  
2. **Classifier**  
   - Fast check: native text layer? (PyMuPDF / pdfminer) → route to text-parsing path or OCR path.  
3. **Preprocessor** (for scanned pages)  
   - PDF → images at 300 DPI (poppler / MuPDF)  
   - Deskew, despeckle, binarize, crop borders, convert to grayscale.  
4. **Layout Analysis**  
   - Use a layout model (LayoutParser / PubLayNet model) to detect paragraphs, headers, tables, forms, captions.  
5. **OCR Engine (Primary)**  
   - Open-source baseline: OCRmyPDF (Tesseract) with tuned models & lang packs.  
   - Optional neural OCR (TrOCR / PaddleOCR) for difficult fonts/handwriting (GPU workers).  
6. **Table & Form Extraction**  
   - Native PDF tables: Camelot / PDFPlumber.  
   - Scanned tables: layout boxes → table parser (Camelot on rasterized region) or model-based table extraction.  
7. **Post-processing & NER**  
   - Language-model or spaCy-based extraction for domain fields, plus regex validators.  
8. **Fallback**  
   - Low-confidence pages → cloud OCR (Google Document AI / AWS Textract / Azure) or human-in-the-loop (HITL).  
9. **Storage & Indexing**  
   - Store extracted text, bounding boxes, full-page images, processing metadata in object store + Postgres (metadata).  
   - Index texts into OpenSearch/Elasticsearch and optionally embeddings to FAISS/Milvus for semantic search.  
10. **Dashboard / Human Review**  
    - Small web UI for human review with re-process/retry/override and audit logs.

## Non-functional requirements
- Throughput: horizontally scalable workers
- Reliability: idempotent processing and robust retry semantics
- Observability: metrics for throughput, error rates, OCR confidence distribution
- Security: encrypted storage in transit & at rest; authenticated APIs (Supabase Auth or JWT)
- Cost control: selective cloud OCR usage based on thresholds

## Directory structure (top-level)
doc-pipeline/
├── infra/ # IaC, k8s manifests, docker-compose, terraform snippets
├── ingest/
│ ├── ingestion-worker/ # watchers/ingesters that push tasks to queue
│ └── sample-ingest-scripts/
├── classifier/ # detect native text vs scanned
├── preprocess/ # image preprocessing tools
├── layout/ # layout detection models + helpers
├── ocr/
│ ├── ocr-workers/ # Tesseract/OCRmyPDF + TrOCR workers
│ └── ocr-adapters/ # adapters for cloud OCR providers
├── extractor/ # table/form extractors (Camelot, PDFPlumber)
├── postprocess/ # NER, normalizers, validators
├── api/ # HTTP API (FastAPI/Express) for upload, status, admin
├── worker-orchestration/ # queue consumer, Celery/K8s jobs
├── web/ # simple frontend (upload + review UI)
├── tests/ # unit+integration test suites
├── docs/ # design docs and runbooks
└── docker/ # Dockerfiles, docker-compose templates


## Important components & files Cursor must create
- `infra/docker-compose.yml` — local compose for Postgres, MinIO (S3), Redis (queue), and ElasticSearch.
- `api/app/main.py` (FastAPI) — endpoints:
  - `POST /upload` — accept PDF upload (multipart); returns doc id + status
  - `GET /status/{doc_id}` — processing status
  - `GET /result/{doc_id}` — returns extracted text, fields, bounding boxes
  - `POST /retry/{doc_id}` — reprocess document
- `classifier/detect_text_layer.py` — returns boolean and heuristics (text length, fonts).
- `preprocess/image_prep.py` — implements deskew, despeckle, binarize, dpi resize.
- `layout/detect_layout.py` — wrapper around LayoutParser + model download.
- `ocr/ocr_worker.py` — primary worker that uses OCRmyPDF/Tesseract, falls back to TrOCR if configured.
- `ocr/cloud_adapters/google_docai.py` and `ocr/cloud_adapters/aws_textract.py` — adapters for cloud calls.
- `extractor/tables.py` — tries PDFPlumber/Camelot on vector pages, otherwise on layout-detected table bbox image.
- `postprocess/ner_extract.py` — spaCy + regex pipelines to extract fields and confidence.
- `worker-orchestration/consumer.py` — queue consumer orchestrating steps and writing to DB + metrics.
- `web/upload_page` — minimal upload UI + progress bar; authentication via Supabase (or basic JWT/local dev).

## Acceptance criteria
- Cursor produces a runnable dev environment via `docker-compose up` that:
  - Accepts uploaded PDFs via API
  - Classifies native vs scanned
  - Runs preprocessing and OCR on scanned docs and produces a searchable text layer
  - Extracts tables from at least 3 different table styles (native vector, bordered raster, borderless raster)
  - Stores metadata and results in Postgres and indexes text to ElasticSearch
  - Provides simple UI to view doc text + bounding boxes + reprocess button
- Includes unit tests for classifier + OCR worker + table extraction and a short benchmark script to evaluate OCR CER on a sample set

## Deployment targets & notes
- Local: Docker Compose (Postgres, MinIO, Redis, ElasticSearch)
- Prod: Kubernetes (Helm charts) or cloud-managed services. Provide Dockerfile for each service and sample k8s Job manifest for batch workers.

## Environment variables (sample)
S3_ENDPOINT=minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
POSTGRES_URL=postgresql://user:pass@postgres:5432/docdb
REDIS_URL=redis://redis:6379
ELASTIC_URL=http://elasticsearch:9200

CLOUD_OCR_GOOGLE_KEY=...
CLOUD_OCR_AWS_ACCESS_KEY=...
CLOUD_OCR_AWS_SECRET=...
OCR_CONF_THRESHOLD=0.85


## Small code snippets (to seed Cursor)
### Detect text layer (Python / PyMuPDF)
```python
import fitz  # PyMuPDF
def has_text_layer(pdf_path, threshold_chars=50):
    doc = fitz.open(pdf_path)
    total = 0
    for p in doc:
        txt = p.get_text("text")
        total += len(txt.strip())
        if total > threshold_chars:
            return True
    return False

Pre-process (deskew + convert to 300dpi, pillow + openCV pseudocode)

# pseudocode
image = load_image(path)
image = deskew(image)
image = denoise(image)
image = resize_to_dpi(image, 300)
image = binarize(image)
save(image, dst)

QA / Benchmark plan

Cursor must produce a tests/benchmark.sh that:

Runs pipeline on 100 mixed PDFs (native + scanned)

Produces CSV with fields: doc_id, chars_extracted, avg_word_confidence, cer_estimate (by comparing to ground-truth where available), time_seconds

Provide README with how to run local demo and expected outputs.
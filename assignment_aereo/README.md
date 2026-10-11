# Bulk Certificate Generator Backend API

A high-performance, asynchronous, resilient Python backend built with **FastAPI**, **SQLite**, **SQLAlchemy**, and **ReportLab** for generating bulk personalized PDF certificates from recipient datasets.

---

## 1. Project Title and Overview

The **Bulk Certificate Generator API** solves the problem of generating high volumes of personalized PDF certificates for workshops, webinars, academic courses, and corporate training programs. Clients can issue a single asynchronous request containing recipient details, track job progress in real time, inspect granular per-recipient status, and download generated certificates.

---

## 2. Problem Statement and Implemented Features

### Problem Statement
Generating certificates individually is slow, prone to manual error, and fragile. Processing bulk requests synchronously can cause HTTP timeout errors, memory spikes, or cascading failures where a single bad record crashes the entire batch.

### Implemented Features
- **Bulk Job Submission**: Submit batch certificate requests with top-level event details and recipient lists.
- **Asynchronous Processing**: Background job execution ensures immediate `HTTP 202 Accepted` response to clients.
- **Resilient Fault Isolation**: Errors during individual PDF generation are caught per-recipient; processing continues for remaining recipients.
- **Granular Progress & Status Tracking**: Live metrics for total, pending, processing, successful, and failed recipients, along with progress percentage.
- **Recipient-Level Results**: Detailed status reporting per recipient, including download URLs for successful items and safe error messages for failures.
- **Secure File Downloads**: Stream generated PDF certificates with path traversal safeguards and content-disposition headers.
- **Comprehensive Data Validation**: Pydantic schemas enforce duplicate certificate ID checks, email formatting, date validation, and maximum batch sizes.
- **Full Test Suite**: 21 automated pytest tests covering schemas, status transitions, failure isolation, PDF layout/text content, persistence, and security.

---

## 3. Technology Stack

- **Language**: Python 3.11+ (Tested on Python 3.12.4)
- **Web Framework**: FastAPI (Async route handlers, background tasks, Swagger UI)
- **Database & ORM**: SQLite with SQLAlchemy 2.x
- **Validation**: Pydantic v2 & `pydantic-settings`
- **PDF Engine**: ReportLab 5.x
- **Testing**: pytest, FastAPI TestClient, HTTPX, `pypdf`
- **Environment**: `python-dotenv`

---

## 4. Architecture and Project Structure

```
assignment_aereo/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Application entry point & exception handlers
│   ├── config.py                # Environment configuration settings
│   ├── database.py              # Database engine, SessionLocal & table initialization
│   ├── models.py                # SQLAlchemy ORM models (GenerationJob, CertificateRecipient)
│   ├── schemas.py               # Pydantic request/response models & validators
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py            # API endpoint definitions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── certificate_service.py # Safe file generation & path traversal protection
│   │   └── job_service.py       # Core business logic & background task worker
│   └── templates/
│       ├── __init__.py
│       └── certificate_template.py # ReportLab PDF canvas design
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures (Isolated SQLite DB & output dirs)
│   ├── test_jobs.py             # Endpoints, job status & persistence tests
│   ├── test_validation.py       # Pydantic schemas, duplicate check & 404/422 tests
│   ├── test_certificates.py     # PDF generation & text content extraction tests
│   └── test_failures.py         # Partial/full failure isolation & security tests
├── generated_certificates/
│   └── .gitkeep                 # Output directory for stored PDF files
├── .env.example                 # Configuration template
├── .gitignore                   # Git ignore settings
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

## 5. Prerequisites

- Python 3.11 or higher
- Git
- `pip` (Python package installer)

---

## 6. Virtual Environment Setup

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### macOS / Linux (Bash / Zsh)
```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 7. Dependency Installation

Upgrade `pip` and install all project dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 8. Environment Configuration

Copy `.env.example` to `.env`:

### Windows (PowerShell)
```powershell
Copy-Item .env.example .env
```

### macOS / Linux
```bash
cp .env.example .env
```

Default settings in `.env`:
```env
APP_NAME="Bulk Certificate Generator API"
ENVIRONMENT="development"
DEBUG=True
API_V1_STR="/api/v1"
DATABASE_URL="sqlite:///./certificates.db"
OUTPUT_DIR="./generated_certificates"
MAX_BATCH_SIZE=100
MAX_STRING_LENGTH=255
```

---

## 9. Database Initialization Behavior

The application automatically creates the SQLite database file (`certificates.db`) and initializes all required tables (`generation_jobs` and `certificate_recipients`) when starting up via the FastAPI `lifespan` handler. No manual SQL migrations or scripts are required for initial setup.

---

## 10. Starting the FastAPI Application

Run the application using Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

The server will start at `http://127.0.0.1:8000`.

---

## 11. API Documentation URLs

- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON Schema**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 12. Submitting a Bulk Generation Request

### Endpoint
`POST /api/v1/certificate-jobs`

### Example Request (`curl`)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/certificate-jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Python Backend Development Workshop",
    "organization_name": "Example Learning Institute",
    "issue_date": "2026-10-10",
    "recipients": [
      {
        "name": "Aarav Sharma",
        "email": "aarav@example.com",
        "certificate_id": "CERT-001"
      },
      {
        "name": "Priya Patel",
        "email": "priya@example.com",
        "certificate_id": "CERT-002"
      }
    ]
  }'
```

### PowerShell Example

```powershell
$body = @{
    event_name = "Python Backend Development Workshop"
    organization_name = "Example Learning Institute"
    issue_date = "2026-10-10"
    recipients = @(
        @{ name = "Aarav Sharma"; email = "aarav@example.com"; certificate_id = "CERT-001" },
        @{ name = "Priya Patel"; email = "priya@example.com"; certificate_id = "CERT-002" }
    )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/certificate-jobs" -Method Post -ContentType "application/json" -Body $body
```

---

## 13. Example API Responses

### `POST /api/v1/certificate-jobs` (`HTTP 202 Accepted`)
```json
{
  "job_id": "ba8378bc-8edb-43c8-b3f6-2e9fc100a7ff",
  "status": "queued",
  "total_recipients": 2,
  "status_url": "/api/v1/certificate-jobs/ba8378bc-8edb-43c8-b3f6-2e9fc100a7ff"
}
```

---

## 14. Checking Job Status and Progress

### Endpoint
`GET /api/v1/certificate-jobs/{job_id}`

### Command
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/certificate-jobs/ba8378bc-8edb-43c8-b3f6-2e9fc100a7ff"
```

### Response Example (`HTTP 200 OK`)
```json
{
  "job_id": "ba8378bc-8edb-43c8-b3f6-2e9fc100a7ff",
  "status": "completed",
  "total_recipients": 2,
  "pending_recipients": 0,
  "processing_recipients": 0,
  "successful_generations": 2,
  "failed_generations": 0,
  "progress_percentage": 100.0,
  "created_at": "2026-10-10T14:23:18.123456Z",
  "completed_at": "2026-10-10T14:23:18.543210Z"
}
```

---

## 15. Retrieving Recipient-Level Results

### Endpoint
`GET /api/v1/certificate-jobs/{job_id}/results`

### Command
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/certificate-jobs/ba8378bc-8edb-43c8-b3f6-2e9fc100a7ff/results"
```

### Response Example (`HTTP 200 OK`)
```json
{
  "job_id": "ba8378bc-8edb-43c8-b3f6-2e9fc100a7ff",
  "total_recipients": 2,
  "results": [
    {
      "name": "Aarav Sharma",
      "email": "aarav@example.com",
      "certificate_id": "CERT-001",
      "status": "success",
      "error_message": null,
      "certificate_download_url": "/api/v1/certificate-jobs/ba8378bc-8edb-43c8-b3f6-2e9fc100a7ff/certificates/CERT-001"
    },
    {
      "name": "Priya Patel",
      "email": "priya@example.com",
      "certificate_id": "CERT-002",
      "status": "success",
      "error_message": null,
      "certificate_download_url": "/api/v1/certificate-jobs/ba8378bc-8edb-43c8-b3f6-2e9fc100a7ff/certificates/CERT-002"
    }
  ]
}
```

---

## 16. Downloading a Generated PDF

### Endpoint
`GET /api/v1/certificate-jobs/{job_id}/certificates/{certificate_id}`

### Command
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/certificate-jobs/ba8378bc-8edb-43c8-b3f6-2e9fc100a7ff/certificates/CERT-001" \
  --output certificate_CERT-001.pdf
```

---

## 17. Running Automated Tests

Run the full test suite with verbose output:

```bash
pytest -v
```

---

## 18. Running Focused Test Files

Run a specific test file:

```bash
# Test schema and data validation rules
pytest tests/test_validation.py -v

# Test PDF layout and text content extraction
pytest tests/test_certificates.py -v

# Test partial/full failure isolation behavior
pytest tests/test_failures.py -v

# Test endpoints and job status transitions
pytest tests/test_jobs.py -v
```

---

## 19. Validation Rules & Failure Handling

### Validation Rules (HTTP 422)
- **Top-Level Fields**: `event_name`, `organization_name`, `issue_date`, and `recipients` are strictly required and cannot be empty or whitespace-only.
- **Date Format**: `issue_date` must conform to ISO format `YYYY-MM-DD`.
- **Batch Size Limit**: Default maximum is 100 recipients per request (configurable via `MAX_BATCH_SIZE`).
- **Duplicate Prevention**: Duplicate `certificate_id` values within the same payload trigger request rejection.
- **Email Validation**: Recipient email must be a valid email string.
- **String Length Limits**: Names, emails, and certificate IDs are capped at 255 characters.

### Partial Failure Isolation Policy
- **Request Level**: Invalid overall payload structures or invalid recipient formatting cause request-level rejection (`422 Unprocessable Entity`).
- **Runtime Generation Level**: Once a request passes validation, the job and recipient records are persisted with status `queued` / `pending`. During background execution, each recipient is processed independently. If rendering a specific certificate raises an exception, only that recipient is marked as `failed` (storing a sanitized error message). The worker continues processing all remaining recipients.
- **Final Job Status**:
  - `completed`: 100% of recipients generated successfully.
  - `completed_with_errors`: At least 1 recipient succeeded and at least 1 recipient failed.
  - `failed`: 100% of recipients failed to generate.

---

## 20. Job & Recipient Status Lifecycle

```
[Job Creation] -> queued -> processing -> completed / completed_with_errors / failed
[Recipient]    -> pending -> processing -> success / failed
```

---

## 21. Architecture & Design Decisions

### In-Process Background Tasks vs Persistent Message Queues
- **Choice**: FastAPI `BackgroundTasks` executing lightweight synchronous PDF rendering worker tasks.
- **Trade-offs**: In-process background processing eliminates external setup complexity (Celery, Redis, RabbitMQ) and provides immediate setup for small-to-medium workloads.
- **Limitation**: In-process tasks run within the app process memory. If the process crashes or restarts during execution, in-flight jobs are interrupted.
- **Production Recommendation**: For massive scale (10,000+ batch items) or multi-node worker clusters, replace FastAPI `BackgroundTasks` with a persistent worker queue such as **Celery** with **Redis/RabbitMQ** or **ARQ**.

---

## 22. Known Limitations & Future Improvements

1. **In-Process Queue**: Crashes during background processing require manual job re-triggering.
2. **Template Customization**: Features a single predefined landscape template. Future enhancements could introduce customizable HTML-to-PDF or Jinja2 template selection.
3. **Storage Backends**: PDF certificates are saved to local disk (`generated_certificates/`). Cloud object storage (AWS S3, Google Cloud Storage) could be added via an abstract storage interface.

---

## 23. Security Considerations

- **Path Traversal Protection**: Certificate IDs are validated using `os.path.basename` and checked to ensure target file paths never escape the configured output directory (`OUTPUT_DIR`).
- **Data Sanitization**: Internal filesystem paths, database queries, and raw Python stack traces are never exposed in API error responses.
- **Input Constraints**: String length caps and batch size bounds prevent memory exhaustion attacks.

---

## 24. Troubleshooting

- **Port Already in Use**: If port 8000 is occupied, run `uvicorn app.main:app --port 8005`.
- **Database Locked Error**: SQLite supports single-writer concurrency. Background tasks and route handlers use thread-safe scoped sessions (`check_same_thread=False`).

---

## 25. End-to-End Workflow Example

1. **Start server**: `uvicorn app.main:app --port 8000`
2. **Check health**: `curl http://127.0.0.1:8000/health`
3. **Submit job**: `POST /api/v1/certificate-jobs` -> Get `job_id`
4. **Poll status**: `GET /api/v1/certificate-jobs/{job_id}` -> Wait for `completed`
5. **Get download links**: `GET /api/v1/certificate-jobs/{job_id}/results`
6. **Download certificate**: `GET /api/v1/certificate-jobs/{job_id}/certificates/{certificate_id}` -> Download PDF file.

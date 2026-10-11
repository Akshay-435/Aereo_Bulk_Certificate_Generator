import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import init_db
from app.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database table creation and directory initialization."""
    init_db()
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="A robust, scalable Bulk Certificate Generator API built with FastAPI, SQLite, and ReportLab.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include API v1 router
app.include_router(api_router)


@app.get(
    "/health",
    summary="Health check",
    description="Returns a simple JSON status indicating that the application is running.",
)
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats validation errors cleanly without exposing internal stack traces."""
    errors = []
    for error in exc.errors():
        loc = " -> ".join([str(loc_part) for loc_part in error.get("loc", []) if loc_part != "body"])
        msg = error.get("msg", "Validation error")
        errors.append(f"{loc}: {msg}" if loc else msg)

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "errors": errors,
        },
    )

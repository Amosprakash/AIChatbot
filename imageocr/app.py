"""
FastAPI application for ImageOCR.
Provides endpoints for multi-format text extraction using OCR.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from contextlib import asynccontextmanager
import time
import uvicorn
import os
from typing import Optional

import log as Log
import upload
from config import config
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set Google Vision credentials if provided
if config.GOOGLE_APPLICATION_CREDENTIALS:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.GOOGLE_APPLICATION_CREDENTIALS


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    Log.log.info("ImageOCR application starting...")
    Log.log.info(f"Configuration: Host={config.APP_HOST}, Port={config.APP_PORT}")

    # Validate configuration
    if not config.validate():
        Log.log.warning("Configuration validation failed - some features may not work")

    yield

    Log.log.info("ImageOCR application shutting down...")


app = FastAPI(
    title="ImageOCR API",
    description="Multi-format intelligent OCR pipeline for text extraction",
    version="2.0.0",
    lifespan=lifespan
)


# Custom validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0].get("msg", "Invalid input")
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"message": first_error},
    )


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True,
)


# Logging middleware
@app.middleware("http")
async def middleware(request: Request, call_next):
    start = time.time()
    try:
        body = await request.json()
    except Exception:
        body = None

    response = await call_next(request)
    process = (time.time() - start) * 1000
    Log.log.info(
        f"{request.method} {request.url.path} | body:{body} | "
        f"statuscode:{response.status_code} | processtime:{process:.2f}ms"
    )
    return response


# Register routers
app.include_router(upload.router, prefix="/api", tags=["Upload"])


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=config.DEBUG
    )

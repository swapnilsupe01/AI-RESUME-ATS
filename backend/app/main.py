"""
AI Resume ATS — Explainable Resume & Project Intelligence System.
FastAPI Application with Prometheus Metrics, Static UI, and CORS.
"""
import os
import time
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.api.routes import router

# ── Prometheus Observability Metrics ─────────────────────────────────────────
REQUEST_COUNT = Counter(
    "http_requests_total", 
    "Total HTTP requests received", 
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", 
    "HTTP request latency in seconds", 
    ["endpoint"]
)
ANALYSIS_COUNT = Counter(
    "resume_analyses_total", 
    "Total resumes analyzed by intelligence engine"
)

# ── App Instance ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Resume ATS — Explainable Resume & Project Intelligence",
    description="Intelligent ATS combining Sentence-BERT Job Matching and Public Project Evidence Verification.",
    version="2.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Prometheus Metrics Middleware ────────────────────────────────────────────
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    endpoint = request.url.path
    REQUEST_COUNT.labels(
        method=request.method, 
        endpoint=endpoint, 
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    
    if endpoint == "/api/analyze" and response.status_code == 200:
        ANALYSIS_COUNT.inc()

    return response

# ── Prometheus Metrics Endpoint ──────────────────────────────────────────────
@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint for cloud observability and health monitoring."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# ── API Router ───────────────────────────────────────────────────────────────
app.include_router(router)

# ── Static Frontend Files ────────────────────────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        """Serve the modern SPA index.html."""
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

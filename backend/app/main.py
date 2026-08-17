"""
AI Resume ATS — FastAPI Application.
Mounts static frontend files and includes the API router.
"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

# ── App Instance ────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Resume ATS",
    description="Intelligent Applicant Tracking System powered by NLP & ML",
    version="1.0.0",
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Router ───────────────────────────────────────────────────────────────
app.include_router(router)

# ── Static Frontend Files ────────────────────────────────────────────────────
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        """Serve the main SPA index.html."""
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

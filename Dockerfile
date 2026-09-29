# =========================================================================
# AI Resume ATS — Production Multi-Stage Dockerfile
# Optimized for Fast Startup, Model Pre-Caching, and Cloud Port Binding
#
# FIX: CPU-only PyTorch wheel index prevents pip from resolving to the
# CUDA torch wheel which pulls in 2.7 GB nvidia/* + 690 MB triton libs
# ("no space left on device" writing libcublasLt.so.13).
# =========================================================================

# Stage 1: Build & Dependencies
FROM python:3.10-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.hf_cache \
    SENTENCE_TRANSFORMERS_HOME=/app/.hf_cache/sentence_transformers

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .

# requirements.txt starts with:
#   --extra-index-url https://download.pytorch.org/whl/cpu
#   torch
# which pins pip to resolve torch to the 196 MB CPU-only wheel, not the
# 2 GB+ CUDA build that ships nvidia/libcublasLt.so.13 et al.
RUN pip install --user --no-warn-script-location -r requirements.txt

# Pre-download the embedding model into the pinned HF_HOME.
# The runner stage copies this cache so startup is fully offline
# (TRANSFORMERS_OFFLINE=1 is set in the runtime stage).
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Final Lightweight Runtime
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.10-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH \
    PYTHONPATH=/app/backend:/app/backend/app \
    PORT=8000 \
    HF_HOME=/app/.hf_cache \
    SENTENCE_TRANSFORMERS_HOME=/app/.hf_cache/sentence_transformers \
    TRANSFORMERS_OFFLINE=1 \
    HF_DATASETS_OFFLINE=1

# curl is required only by the HEALTHCHECK probe
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from the builder stage
COPY --from=builder /root/.local /root/.local

# Copy the pre-cached Hugging Face / Sentence-Transformers model
COPY --from=builder /app/.hf_cache /app/.hf_cache

# Copy application source code
COPY backend ./backend
COPY dataset ./dataset

# Expose default port (and dynamic $PORT on Sevalla / Render)
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# Start FastAPI server using dynamic $PORT variable
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --app-dir backend

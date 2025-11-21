# docker/Dockerfile
#
# Multi-stage Dockerfile with optimized targets:
#   - api          : FastAPI backend (CPU-only, no email intelligence)
#   - api_email_gpu: FastAPI backend with email intelligence (GPU-enabled)
#   - ui           : Gradio UI (CPU-only, no email intelligence)
#
# GPU support is handled by the Ollama container and the api_email_gpu target.

# =========================
# Builder stage
# =========================
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only what's needed for installation
COPY pyproject.toml ./
COPY llumdocs ./llumdocs

# Install project in a virtual environment
RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade pip \
    && /venv/bin/pip install . \
    && find /venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true \
    && find /venv -name "*.pyc" -delete

# =========================
# Runtime base (CPU-only, no build tools)
# =========================
FROM python:3.12-slim AS runtime

ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /venv /venv

# Copy only the source code (no tests, docs, etc.)
COPY llumdocs ./llumdocs

# =========================
# API image (CPU-only, no email intelligence)
# =========================
FROM runtime AS api

# Align with .env.template default
ENV HF_HOME=/models/hf

RUN mkdir -p /models/hf

EXPOSE 8000

# Use uvicorn directly. In production you can raise workers via env or override CMD.
CMD ["uvicorn", "llumdocs.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

# ==========================================
# API image with email intelligence (GPU-enabled)
# ==========================================
FROM runtime AS api_email_gpu

ENV HF_HOME=/models/hf \
    LLUMDOCS_ENABLE_EMAIL_INTEL="true" \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# We need pyproject.toml to install the [email] extra
COPY pyproject.toml ./

# Install build tools temporarily, then install [email] extra and clean up
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
 && pip install --no-cache-dir ".[email]" \
 && apt-get remove -y build-essential \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/* /root/.cache/pip \
 && find /venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true \
 && find /venv -name "*.pyc" -delete

RUN mkdir -p /models/hf

EXPOSE 8000

CMD ["uvicorn", "llumdocs.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

# ==========================================
# API image with bundled HuggingFace models (legacy, CPU-only)
# ==========================================
FROM runtime AS api_hf

ENV HF_HOME=/models/hf

RUN mkdir -p /models/hf

# Install email intelligence extra (required for HF models)
RUN pip install --no-cache-dir ".[email]"

# Pre-download email intelligence models so the container is "warm".
# This avoids paying the download cost on first request.
RUN python -c "from llumdocs.services.email_intelligence_service import DEFAULT_EMAIL_ROUTING_LABELS, classify_email, detect_phishing, analyze_sentiment; classify_email('Test message about billing and support.', DEFAULT_EMAIL_ROUTING_LABELS); detect_phishing('This is a harmless test email.'); analyze_sentiment('Això és una prova fantàstica.')"

EXPOSE 8000

CMD ["uvicorn", "llumdocs.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

# =========================
# Gradio UI image (CPU-only, with email intelligence)
# =========================
FROM runtime AS ui

ENV HF_HOME=/models/hf \
    LLUMDOCS_ENABLE_EMAIL_INTEL="true" \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# We need pyproject.toml to install the [email] extra
COPY pyproject.toml ./

# Install build tools temporarily, then install [email] extra and clean up
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
 && pip install --no-cache-dir ".[email]" \
 && apt-get remove -y build-essential \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/* /root/.cache/pip \
 && find /venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true \
 && find /venv -name "*.pyc" -delete

RUN mkdir -p /models/hf

EXPOSE 7860

# Run the Gradio entrypoint
CMD ["python", "-m", "llumdocs.ui.main"]

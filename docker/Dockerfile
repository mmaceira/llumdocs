# docker/Dockerfile
#
# Multi-stage Dockerfile with shared CPU-only base and three targets:
#   - api      : FastAPI backend
#   - api_hf   : FastAPI backend with HuggingFace models pre-downloaded
#   - ui       : Gradio UI
#
# All stages are CPU-only; GPU is handled by the Ollama container.

# =========================
# Base image (CPU-only)
# =========================
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# System deps (minimal; extend if you hit missing libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install LlumDocs into the image
# (we copy only what is needed to install the package)
COPY pyproject.toml README.md ./
COPY llumdocs ./llumdocs

RUN pip install --no-cache-dir .

# =========================
# API image (FastAPI, CPU)
# =========================
FROM base AS api

# Align with .env.template default
ENV HF_HOME=/models/hf

RUN mkdir -p /models/hf

# Install email intelligence extra (required for HF models)
RUN pip install --no-cache-dir ".[email]"

EXPOSE 8000

# Use uvicorn directly. In production you can raise workers via env or override CMD.
CMD ["uvicorn", "llumdocs.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

# ==========================================
# API image with bundled HuggingFace models
# ==========================================
FROM base AS api_hf

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
# Gradio UI image
# =========================
FROM base AS ui

# Install email intelligence extra (required for email intelligence feature in UI)
RUN pip install --no-cache-dir ".[email]"

EXPOSE 7860

# Run the Gradio entrypoint
CMD ["python", "-m", "llumdocs.ui.main"]

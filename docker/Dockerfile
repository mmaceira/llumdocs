FROM python:3.12-slim AS base

# Install system deps for Tesseract, OCR engines, PDFs, images
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast package installer)
RUN pip install uv

# Create workdir
WORKDIR /app

# Copy project files
COPY . .

# Install Python deps using pyproject, including UI and email extras
RUN uv sync --frozen --extra ui --extra email

# Copy helper script to wait for Ollama to be ready
COPY docker/wait-for-ollama.sh /usr/local/bin/wait-for-ollama
RUN chmod +x /usr/local/bin/wait-for-ollama

# Expose Gradio / FastAPI ports
EXPOSE 7860 8000

# Default command is controlled by docker-compose to run both API and UI
CMD ["bash", "-lc", "honcho -f docker/Procfile start"]

FROM python:3.12-slim AS base

# Install system deps for Tesseract, OCR engines, PDFs, images
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast package installer)
RUN pip install uv

# Create workdir
WORKDIR /app

# Copy project files
COPY . .

# Install Python deps using pyproject, including UI and email extras
RUN uv sync --frozen --extra ui --extra email

# Expose Gradio / FastAPI port
EXPOSE 7860

# Default command - use the same entrypoint as local UI (`uv run llumdocs-ui`)
CMD ["uv", "run", "llumdocs-ui"]

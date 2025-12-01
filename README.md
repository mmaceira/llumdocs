# LlumDocs — OCR + LLM document intelligence, with API + UI

> End-to-end document processing (OCR, extraction, translation) exposed via a FastAPI backend and a Gradio v4 UI.

[![Python](https://img.shields.io/badge/python-3.12-3776AB.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-%F0%9F%9A%80-009688.svg)](https://fastapi.tiangolo.com/)
[![Gradio](https://img.shields.io/badge/gradio-v4-3A86FF.svg)](https://www.gradio.app/)
[![Docker Compose](https://img.shields.io/badge/docker-compose-0db7ed.svg)](https://docs.docker.com/compose/)

---

## TL;DR

**Local (uv):**

```bash
# Install deps (UI + dev tools)
uv sync --extra ui --extra dev

# UI
uv run llumdocs-ui
# -> http://localhost:7860

# API (optional, in another terminal)
uv run llumdocs-api
# or: uv run uvicorn llumdocs.api.app:app --reload
# -> http://localhost:8000 (OpenAPI at /docs)
```

**Docker (CPU profiles shown):**

```bash
cd docker

docker compose --profile cpu --profile ui up --build

# -> API on http://localhost:8000
# -> UI  on http://localhost:7860
```

**Smoke test translate:**

```bash
curl -s -X POST "http://localhost:8000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello, how are you?","source_lang":"en","target_lang":"ca"}'
```

---

## Features

* ⚡ FastAPI backend with OpenAPI docs
* 🧠 Gradio **v4** UI (Blocks/Components)
* 🔤 Translation (ca/es/en + autodetect) via `/api/translate`
* 👁️ OCR + (LLM-assisted) extraction pipeline for delivery notes, bank statements, payroll
* 🧾 Document summarization, keyword extraction, text transformation (simplify, technical, company tone)
* 🖼️ Image description using vision models
* 📧 Email intelligence (routing, phishing detection, sentiment) via optional extra
* 🐳 Docker Compose profiles for API + UI + Ollama (CPU/GPU and HF-bundled variants)
* 🔧 Clean dev flow with `uv` (sync, run, test, lint)

---

## Architecture

```text
[UI: Gradio v4]  <---->  [Services: Python modules]  <---->  [LLM backends (OpenAI/Ollama)]
       │
       └────────────── (parallel) ──────────────>  [API: FastAPI (HTTP)]
```

* The Gradio UI uses the Python services directly (`llumdocs/services`) for low-latency, rich interactions.
* The FastAPI app exposes a stable HTTP API (`/api/translate`, `/api/text/*`, `/api/images/*`, `/api/documents/*`).
* Docker Compose wires UI, API, and Ollama together into a single stack.
* For a deeper dive, see `docs/ARCHITECTURE.md`.

---

## Install & Run

### Prerequisites

* Python **3.12+**
* [`uv`](https://github.com/astral-sh/uv)
* Docker + Docker Compose (optional, for containerized runs)
* (Optional) GPU drivers + NVIDIA Container Toolkit for GPU profiles

### Local (uv)

```bash
# 1) Install deps
uv sync --extra ui --extra dev

# 2) (Optional) also install email intelligence extras
uv sync --extra email

# 3) Start API (terminal 1)
uv run llumdocs-api
# or: uv run uvicorn llumdocs.api.app:app --reload
# -> http://localhost:8000 (OpenAPI at /docs, health at /health)

# 4) Start UI (terminal 2)
uv run llumdocs-ui
# -> http://localhost:7860
```

The UI runs directly against the Python services; the API is useful when you want to integrate LlumDocs over HTTP from other systems.

### Docker Compose (CPU)

```bash
cd docker

docker compose --profile cpu --profile ui up --build
```

This starts:

* `api` – FastAPI on `http://localhost:8000`
* `ui` – Gradio on `http://localhost:7860`
* `ollama` – Local LLM server (mapped from `11435` on the host)

Profiles:

* `cpu` – CPU-only API + Ollama
* `gpu` – GPU-enabled API with email intelligence
* `ui` – Gradio UI
* `hf-bundled` – API with HuggingFace models baked into the image

Stop the stack with:

```bash
docker compose down
```

---

## Configuration

Create a `.env` in the project root (or configure via your shell) with e.g.:

```env
# API server
LLUMDOCS_HOST=0.0.0.0
LLUMDOCS_PORT=8000
LLUMDOCS_RELOAD=true

# CORS for the API (comma-separated origins)
LLUMDOCS_CORS_ORIGINS=http://localhost:7860,http://localhost:8000

# LLM backends
OPENAI_API_KEY=...
OLLAMA_API_BASE=http://localhost:11434  # or http://ollama:11434 in Docker

# Optional: UI launch config
LLUMDOCS_UI_HOST=0.0.0.0
LLUMDOCS_UI_PORT=7860
LLUMDOCS_UI_SHARE=false
```

In Docker, `docker/docker-compose.yml`:

* Mounts `../.env` into API and UI containers.
* Sets `OLLAMA_API_BASE` and `LLUMDOCS_API_URL=http://api:8000` for the UI.

See `docs/INSTALL.md` for a more detailed environment guide and model recommendations.

---

## API

* OpenAPI / Swagger: `http://localhost:8000/docs`
* Health: `GET /health`
* Readiness: `GET /ready`

### Example — Translate

```bash
curl -s -X POST "http://localhost:8000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello, how are you?","source_lang":"en","target_lang":"ca"}'
```

### Example — Keywords

```bash
curl -s -X POST "http://localhost:8000/api/text/keywords" \
  -H "Content-Type: application/json" \
  -d '{"text":"Large language models power many modern NLP applications."}'
```

More endpoints (summaries, text transformation, image description, document extraction) are described in the interactive docs.

---

## Development

### Gradio v4 note

* `gr.Blocks(css=...)` was removed in v4. LlumDocs injects CSS via:

  ```python
  with gr.Blocks(title="LlumDocs") as demo:
      gr.HTML(f"<style>{FEATURE_BUTTON_CSS}</style>", visible=False)
  ```

* Component `.style(...)` helpers are largely deprecated. Prefer CSS via `elem_classes` / `elem_id`.

### Common tasks

```bash
# Install all dev tooling
uv sync --extra ui --extra dev --extra email

# Lint / format
uv run ruff check .
uv run ruff format .

# Tests
uv run pytest

# Run only integration tests
uv run pytest -m integration
```

If you use `pre-commit`, install hooks with:

```bash
uv run pre-commit install
```

See `docs/TESTING.md` for more detailed testing guidance.

---

## Troubleshooting

**Port already in use (8000 / 7860)**

```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

**UI can’t reach models / backend**

* Ensure your `.env` sets `OPENAI_API_KEY` or `OLLAMA_API_BASE` correctly.
* In Docker, confirm the `ollama` container is healthy (`docker ps` and `docker logs ollama`).

**Gradio error:** `TypeError: BlockContext.__init__() got an unexpected keyword argument 'css'`

* You’re on Gradio v4; remove the `css=` kwarg and inject CSS with `<style>...</style>` as shown above.

**CORS errors in browser**

* Adjust `LLUMDOCS_CORS_ORIGINS` so it includes `http://localhost:7860` (and any other frontends).

**Ollama/models not available**

* Check the `ollama` service logs; ensure models are pulled and that the container has enough VRAM/RAM.

For more Docker-specific tips (GPU, HF-bundled images, model caching), see `docker/README.md`.

---

## Project structure

```text
llumdocs/
  api/                    # FastAPI app (routers, CORS, health/ready)
  document_extraction/    # OCR pipelines, models, visualizers
  services/               # Translation, text tools, image description, email intelligence
  ui/                     # Gradio v4 UI (Blocks, panels, layout)
  llm.py                  # LiteLLM / model selection helpers

docker/
  docker-compose.yml      # API, UI, Ollama, profiles (cpu/gpu/hf-bundled)
  Dockerfile              # Multi-stage build for api/ui images

docs/
  ARCHITECTURE.md         # High-level architecture notes
  INSTALL.md              # Detailed installation & config
  TESTING.md              # How to run tests (unit + integration)

tests/
  ...                     # Unit + integration tests

pyproject.toml            # Project metadata, deps, scripts
README.md                 # You are here
```

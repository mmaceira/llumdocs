 # LlumDocs

LlumDocs is a FastAPI + Gradio toolkit that turns raw documents, text and images into structured knowledge. It wraps LiteLLM so you can swap between OpenAI and Ollama models without touching the business logic.

---

## Quickstart

Once dependencies and your `.env` are set up (see `docs/INSTALL.md`):

```bash
# 1. Launch the Gradio UI
uv run llumdocs-ui

# 2. (Optional) Launch FastAPI in another terminal
uv run uvicorn llumdocs.api.app:app --reload

# Then open http://localhost:7860 for the UI.
# FastAPI will default to http://127.0.0.1:8000 with OpenAPI docs at /docs.
```

---

## Implemented Capabilities

| Capability | Algorithms / Services | API & UI surfacing |
| --- | --- | --- |
| Text translation (ca/es/en + autodetect) | `llumdocs/services/translation_service.py` | `POST /api/translate`, Gradio **Translate** tab |
| Plain-language rewrite | `llumdocs/services/text_transform_service/simplify.py` | `POST /api/text/plain`, Gradio **Plain language** tab |
| Technical rewrite | `llumdocs/services/text_transform_service/technical.py` | `POST /api/text/technical`, Gradio **Technical tone** tab |
| Document summarization (short/executive) | `llumdocs/services/text_transform_service/summary.py` | `POST /api/documents/summarize`, Gradio **Summaries** tab |
| Keyword extraction | `llumdocs/services/text_transform_service/keywords.py` | `POST /api/text/keywords`, Gradio **Keywords** tab |
| Image description (caption + detail) | `llumdocs/services/image_description_service.py` | `POST /api/images/describe`, Gradio **Image description** tab |
| Email intelligence (routing, phishing, sentiment) | `llumdocs/services/email_intelligence_service.py` – HuggingFace zero-shot + phishing + multilingual sentiment | Gradio **Email intelligence** tab (API route planned) |

All endpoints are registered in `llumdocs/api/app.py`, and the Gradio UI lives in `llumdocs/ui/main.py`.

---

## Ways to Use LlumDocs

- **Docker** – Use Docker Compose for easy deployment with all services (API, UI, Ollama). See `docker/README.md` for detailed setup instructions including CPU/GPU profiles and model management.
- **Gradio UI** – Launch `python -m llumdocs.ui.main` to get a multi-tab interface that exposes each utility with minimal inputs. Great for demos and non-technical teammates.
- **REST API** – Run `uv run uvicorn llumdocs.api.app:app --reload` (or `uvicorn llumdocs.api.app:app`) and call endpoints such as `POST /api/translate` or `POST /api/text/keywords`. Responses are JSON-friendly for ERP/RPA integration.
- **Python services** – Import the services directly (`from llumdocs.services.translation_service import translate_text`) to embed transformations inside automations or background jobs.

### API Example

```bash
# Translate text
curl -X POST "http://localhost:8000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "source_lang": "en",
    "target_lang": "ca"
  }'
```

```python
# Python client example
import requests

response = requests.post(
    "http://localhost:8000/api/translate",
    json={
        "text": "Hello, how are you?",
        "source_lang": "en",
        "target_lang": "ca"
    }
)
print(response.json()["translated_text"])
```

---

## Quick Install (see `docs/INSTALL.md` for full guide)

1. **Prereqs** – Python ≥ 3.12, `uv` package manager, optional Ollama + OpenAI credentials.
2. **Install** – `uv sync && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).
   - For email intelligence: `pip install "llumdocs[email]"` (includes `torch` and `transformers`)
3. **Configure** – Copy `.env.template` to `.env`, set `OPENAI_API_KEY`, `LLUMDOCS_DEFAULT_MODEL`, and any Ollama overrides.
4. **Verify** – `uv run uvicorn llumdocs.api.app:app --reload` and hit `http://localhost:8000/health`. Detailed steps, LiteLLM tips, and troubleshooting live in `docs/INSTALL.md`.

## Docker Deployment

LlumDocs includes Docker Compose configurations for easy deployment with all services (API, UI, Ollama, and email intelligence models).

**Quick start:**
```bash
cd docker
docker compose --profile cpu --profile ui up --build
```

This starts:
- FastAPI API on http://localhost:8000
- Gradio UI on http://localhost:7860
- Ollama service (or connects to host Ollama)
- Email intelligence with HuggingFace models

**Available profiles:**
- `--profile cpu` – CPU-only setup
- `--profile gpu` – GPU acceleration (requires NVIDIA Container Toolkit)
- `--profile ui` – Include Gradio UI
- `--profile hf-bundled` – Pre-download HuggingFace models during build

**Full documentation:** See `docker/README.md` for detailed setup, model management, troubleshooting, and environment configuration.

## Recommended Models

| Use case     | Recommended model ids        |
|--------------|------------------------------|
| Text tools   | `gpt-4o-mini` or `ollama/llama3.1:8b` |
| Vision tools | `o4-mini` or `ollama/qwen3-vl:8b` |

See `docs/INSTALL.md` for full model configuration options.

---

## Code Organization

- `llumdocs/services` – Business logic for translation, summaries, keywords, rewrites, image descriptions, and email intelligence pipelines.
- `llumdocs/api` – FastAPI routers that expose each service over HTTP.
- `llumdocs/ui` – Gradio Blocks UI composed of shared components.
- `tests` – Unit suites plus `tests/integration/` for live LLM checks.
- `docs` – In-depth guides (`INSTALL`, `TESTING`, feature specs, roadmap).

---

## Stability & Feature Status

**Core (stable):**
- Translation (ca/es/en)
- Document summarization
- Text simplification
- Technical rewrite
- Keyword extraction

**Experimental:**
- Email intelligence (requires Hugging Face models via `llumdocs[email]` extra)
- Ollama vision models (requires local Ollama setup)

## Documentation Map

- Detailed install & environment setup: `docs/INSTALL.md`
- Running unit/integration suites: `docs/TESTING.md`
- Feature specs & roadmap: `docs/LLM_FEATURE_SPECS.md`
- Development standards & workflows: `docs/LLM_DEVELOPMENT_GUIDE.md`
- High-level positioning and messaging: `docs/LLM_GUIDE_GLOBAL.md`

Have questions or want to plug a new capability? Open an issue or drop a note in `docs/LLM_FEATURE_SPECS.md` before starting new work.

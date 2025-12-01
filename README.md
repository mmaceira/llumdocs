 # LlumDocs

LlumDocs is a FastAPI + Gradio toolkit that turns raw documents, text and images into structured knowledge. It wraps LiteLLM so you can swap between OpenAI and Ollama models without touching the business logic.

## Key Features

LlumDocs provides a comprehensive suite of AI-powered document processing and text transformation capabilities:

- **🌐 Text Translation** – Translate between Catalan, Spanish, and English with automatic language detection. Perfect for multilingual workflows and content localization.

- **✍️ Text Transformation** – Rewrite text in different styles:
  - **Plain language** – Simplify complex text for general audiences (child/teen/adult reading levels)
  - **Technical tone** – Elevate formality and technicality, optionally scoped to specific domains
  - **Company tone** – Adapt text to match your organization's communication style

- **📄 Document Summarization** – Generate concise summaries from long documents:
  - **Short summaries** – Quick overviews for fast scanning
  - **Executive summaries** – High-level insights for decision-makers

- **🔑 Keyword Extraction** – Automatically extract key terms, concepts, and phrases from documents to identify main topics and themes.

- **🖼️ Image Description** – Generate detailed captions and descriptions for images using vision models. Supports both brief captions and comprehensive analyses.

- **📋 Document Extraction** – Extract structured data from business documents:
  - Delivery notes
  - Bank statements
  - Payroll documents
  - Uses OCR for scanned documents

- **📧 Email Intelligence** – Analyze emails for business automation:
  - **Routing** – Classify emails by category and priority
  - **Phishing detection** – Identify suspicious emails
  - **Sentiment analysis** – Multilingual sentiment detection

All features are accessible through a user-friendly Gradio UI, REST API endpoints, or direct Python service imports for integration into your workflows.

![Document Summary](docs/images/document_summary.png)

*Example: Document summarization interface showing how LlumDocs processes and summarizes long documents into concise insights.*

---

## Quickstart

Once dependencies and your `.env` are set up (see `docs/INSTALL.md`):

```bash
# 1. Launch the Gradio UI
uv run llumdocs-ui

# Note: The Gradio UI talks directly to the Python service layer in
# `llumdocs/services` and does NOT use the FastAPI HTTP API. You only
# need FastAPI if you want to call LlumDocs over HTTP from other
# applications or systems.

# 2. (Optional) Launch FastAPI in another terminal
uv run uvicorn llumdocs.api.app:app --reload

# Then open:
# - http://localhost:7860 for the Gradio UI
# - http://localhost:8000/docs for the interactive API documentation (Swagger UI)
```

---

## Implemented Capabilities

| Capability | Algorithms / Services | API & UI surfacing |
| --- | --- | --- |
| Text translation (ca/es/en + autodetect) | `llumdocs/services/translation_service.py` | `POST /api/translate`, Gradio **Translate** tab |
| Plain-language rewrite | `llumdocs/services/text_transform_service/simplify.py` | `POST /api/text/plain`, Gradio **Plain language** tab |
| Technical rewrite | `llumdocs/services/text_transform_service/technical.py` | `POST /api/text/technical`, Gradio **Technical tone** tab |
| Company tone rewrite | `llumdocs/services/text_transform_service/company_tone.py` | Gradio **Text transformation** tab (company tone option) |
| Document summarization (short/executive) | `llumdocs/services/text_transform_service/summary.py` | `POST /api/documents/summarize`, Gradio **Summaries** tab |
| Keyword extraction | `llumdocs/services/text_transform_service/keywords.py` | `POST /api/text/keywords`, Gradio **Keywords** tab |
| Image description (caption + detail) | `llumdocs/services/image_description_service.py` | `POST /api/images/describe`, Gradio **Image description** tab |
| Document extraction (delivery notes, bank statements, payroll) | `llumdocs/services/document_extraction_service.py` | `POST /api/documents/extract`, Gradio **Document extraction** tab |
| Email intelligence (routing, phishing, sentiment) | `llumdocs/services/email_intelligence_service.py` – HuggingFace zero-shot + phishing + multilingual sentiment | Gradio **Email intelligence** tab (API route planned) |

All endpoints are registered in `llumdocs/api/app.py`, and the Gradio UI lives in `llumdocs/ui/main.py`.

---

## Ways to Use LlumDocs

- **Docker** – Use Docker Compose for easy deployment with all services (API, UI, Ollama). See `docker/README.md` for detailed setup instructions including CPU/GPU profiles and model management.
- **Gradio UI** – Launch `uv run llumdocs-ui` (or `python -m llumdocs.ui.main`) to get a multi-tab interface that exposes each utility with minimal inputs. Great for demos and non-technical teammates.
- **REST API** – Run `uv run llumdocs-api` (or `uv run uvicorn llumdocs.api.app:app --reload`) and call endpoints such as `POST /api/translate` or `POST /api/text/keywords`. Responses are JSON-friendly for ERP/RPA integration.
- **Python services** – Import the services directly (`from llumdocs.services.translation_service import translate_text`) to embed transformations inside automations or background jobs.

### Interactive API Documentation (Swagger UI)

Once the FastAPI server is running, visit **`http://localhost:8000/docs`** for interactive API documentation powered by Swagger UI. This interface allows you to:

- **Browse all endpoints** – See all available POST endpoints with their parameters
- **View examples** – Each endpoint includes example request bodies with accepted values
- **Test endpoints directly** – Use the "Try it out" button to send requests and see responses
- **Copy curl commands** – Each endpoint's documentation includes ready-to-use curl examples
- **Understand schemas** – View request/response models with field descriptions and constraints

The Swagger UI automatically includes all the examples and accepted values we've configured, making it easy to explore and test the API without writing code.

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

## Model Unloading

LlumDocs sets `keep_alive=0` for all Ollama requests (via LiteLLM and direct calls) to unload models immediately after inference. This frees VRAM/RAM between calls, which is especially useful when running multiple models or when GPU memory is limited.

**Trade-off:** The first token latency on subsequent calls will be higher due to model reload, but memory is freed between requests.

**Override:** If you need to keep models loaded for faster subsequent calls, you can set a per-model `keep_alive` value in your LiteLLM configuration (e.g., `keep_alive: "300s"` for 5 minutes). However, this is not recommended for production deployments with limited resources.

**Configuration examples:**

```yaml
# LiteLLM YAML config (if using model_list)
model_list:
  - model_name: "llama3.1"
    litellm_params:
      model: "ollama_chat/llama3.1:8b"
      api_base: "http://localhost:11434"
      keep_alive: 0
```

```python
# Python config (llumdocs/llm.py automatically sets this)
from litellm import completion

response = completion(
    model="ollama/llama3.1:8b",
    messages=[{"role": "user", "content": "Hello"}],
    api_base="http://localhost:11434",
    keep_alive=0  # Automatically set by llumdocs.llm
)
```

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
- GUI screenshots gallery: `docs/GUI_SCREENSHOTS.md`

Have questions or want to plug a new capability? Open an issue or drop a note in `docs/LLM_FEATURE_SPECS.md` before starting new work.

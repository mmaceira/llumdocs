 # LlumDocs

LlumDocs is a FastAPI + Gradio toolkit that turns raw documents, text and images into structured knowledge. It wraps LiteLLM so you can swap between OpenAI and Ollama models without touching the business logic.

---

## Implemented Capabilities

| Capability | Algorithms / Services | API & UI surfacing |
| --- | --- | --- |
| Text translation (ca/es/en + autodetect) | `llumdocs/services/translation_service.py` | `/api/translate`, Gradio **Translate** tab |
| Plain-language rewrite | `llumdocs/services/text_transform_service.py` (`simplify`) | `/api/text/plain`, Gradio **Plain language** tab |
| Technical rewrite | `text_transform_service.py` (`technical`) | `/api/text/technical`, Gradio **Technical tone** tab |
| Document summarization (short/executive) | `text_transform_service.py` (`summary`) | `/api/documents/summarize`, Gradio **Summaries** tab |
| Keyword extraction | `text_transform_service.py` (`keywords`) | `/api/text/keywords`, Gradio **Keywords** tab |
| Image description (caption + detail) | `services/image_description_service.py` | (API endpoint coming soon), wired in service layer |

All endpoints are registered in `llumdocs/api/app.py`, and the Gradio UI lives in `llumdocs/ui/main.py`.

---

## Ways to Use LlumDocs

- **Gradio UI** – Launch `python -m llumdocs.ui.main` to get a multi-tab interface that exposes each utility with minimal inputs. Great for demos and non-technical teammates.
- **REST API** – Run `uv run uvicorn llumdocs.api.app:app --reload` (or `uvicorn llumdocs.api.app:app`) and call endpoints such as `POST /api/translate` or `POST /api/text/keywords`. Responses are JSON-friendly for ERP/RPA integration.
- **Python services** – Import the services directly (`from llumdocs.services.translation_service import translate_text`) to embed transformations inside automations or background jobs.

---

## Quick Install (see `docs/INSTALL.md` for full guide)

1. **Prereqs** – Python ≥ 3.12, `uv` package manager, optional Ollama + OpenAI credentials.
2. **Install** – `uv sync && source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).
3. **Configure** – Copy `.env.template` to `.env`, set `OPENAI_API_KEY`, `LLUMDOCS_DEFAULT_MODEL`, and any Ollama overrides.
4. **Verify** – `uv run uvicorn llumdocs.api.app:app --reload` and hit `http://localhost:8000/health`. Detailed steps, LiteLLM tips, and troubleshooting live in `docs/INSTALL.md`.

---

## Code Organization

- `llumdocs/services` – Business logic for translation, summaries, keywords, rewrites, and image descriptions.
- `llumdocs/api` – FastAPI routers that expose each service over HTTP.
- `llumdocs/ui` – Gradio Blocks UI composed of shared components.
- `tests` – Unit suites plus `tests/integration/` for live LLM checks.
- `docs` – In-depth guides (`INSTALL`, `TESTING`, feature specs, roadmap).

---

## Documentation Map

- Detailed install & environment setup: `docs/INSTALL.md`
- Running unit/integration suites: `docs/TESTING.md`
- Feature specs & roadmap: `docs/LLM_FEATURE_SPECS.md`
- Development standards & workflows: `docs/LLM_DEVELOPMENT_GUIDE.md`
- High-level positioning and messaging: `docs/LLM_GUIDE_GLOBAL.md`

Have questions or want to plug a new capability? Open an issue or drop a note in `docs/LLM_FEATURE_SPECS.md` before starting new work.

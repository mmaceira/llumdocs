 # Installing LlumDocs

This guide walks through getting a local development environment ready, including optional Ollama + OpenAI providers and LiteLLM helpers. If you only need the short version, see the Quick Install section in the root `README.md`.

---

## 1. Requirements

- Python **3.12+** (matches `pyproject.toml`)
- [`uv`](https://docs.astral.sh/uv/) for dependency management
- Optional but recommended:
  - [Ollama](https://ollama.ai) for local text and vision models (`llama3.1:8b`, `qwen3-vl:8b`)
  - OpenAI account & `OPENAI_API_KEY`

---

## 2. Clone & Install

```bash
git clone https://github.com/mmaceira/LlumDocs.git
cd LlumDocs

# Install uv if you do not have it yet
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create the virtualenv and install base deps
uv sync

# Recommended for full dev setup (UI + tools)
uv sync --extra ui --extra dev

# Optional: email intelligence extras (large, torch+transformers)
uv sync --extra email

# (Optional) activate the virtualenv if you prefer direct python/pytest usage
source .venv/bin/activate            # Windows: .venv\Scripts\activate
```

`uv sync` reads `pyproject.toml`, creates `.venv`, and installs runtime dependencies. Extras such as `ui`, `dev`, and `email` are enabled via `--extra <name>`.

### Email Intelligence (Optional Extra)

The **email intelligence** feature (routing, phishing detection, sentiment analysis) requires `torch` and `transformers`, which are large packages (~2-3 GB). These are now available as an optional extra:

```bash
# Install with email intelligence support
pip install "llumdocs[email]"

# Or with uv
uv sync --extra email
```

If you don't need email intelligence, you can install the base package without these dependencies:

```bash
# Base installation (no email intelligence)
uv sync
```

The email intelligence service will raise a clear error if used without the `email` extra installed. You can also disable it via environment variable:

```bash
export LLUMDOCS_ENABLE_EMAIL_INTELLIGENCE=0
```

For most use cases (translation, summaries, keywords, image descriptions), the email extra is not required.

### Optional: Email intelligence models (Hugging Face)

The email intelligence service (requires `llumdocs[email]` extra) loads three Hugging Face pipelines:

- Zero-shot routing: `MoritzLaurer/bge-m3-zeroshot-v2.0`
- Phishing detection: `cybersectony/phishing-email-detection-distilbert_v2.1`
- Sentiment: `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`

These can be overridden via environment variables:

```bash
export LLUMDOCS_EMAIL_ZEROSHOT_MODEL="your-org/your-zeroshot-model"
export LLUMDOCS_EMAIL_PHISHING_MODEL="your-org/your-phishing-model"
export LLUMDOCS_EMAIL_SENTIMENT_MODEL="your-org/your-sentiment-model"
```

**Hugging Face cache control:**

Models are downloaded to the default Hugging Face cache directory. In Docker/K8s deployments, you can control the cache location:

```bash
export HF_HOME=/models/hf
# Or set LLUMDOCS_HF_HOME to override (if supported in future versions)
```

Mount a persistent volume at `/models/hf` to avoid re-downloading models on container restarts.

The first call to each capability will be slower (model download + load). Subsequent calls reuse the cached pipeline. Pipelines are thread-safe and reused across requests, but for high-throughput deployments, consider running email intelligence in a dedicated worker process.

---

## 3. Environment Variables

Copy the template, then edit values as needed:

```bash
cp .env.template .env
```

Environment variables are defined in the codebase. See:
- `llumdocs/llm.py` – LLM configuration (models, timeouts, Ollama settings)
- `llumdocs/api/app.py` – API configuration (host, port, CORS)
- `llumdocs/ui/main.py` – UI configuration (host, port, sharing)
- `llumdocs/services/email_intelligence_service.py` – Email intelligence settings
- `llumdocs/api/image_endpoints.py` – Image upload limits

**Recommended models:**

| Use case     | Recommended model ids        |
|--------------|------------------------------|
| Text tools   | `gpt-4o-mini` or `ollama/llama3.1:8b` |
| Vision tools | `o4-mini` or `ollama/qwen3-vl:8b` |

**Minimal `.env` example:**

```ini
OPENAI_API_KEY=sk-your-key
LLUMDOCS_DEFAULT_MODEL=gpt-4o-mini
LLUMDOCS_DEFAULT_VISION_MODEL=o4-mini
```

---

## 4. Configure LiteLLM Providers

### Ollama

**Model Unloading:** LlumDocs automatically sets `keep_alive=0` for all Ollama requests to unload models immediately after inference, freeing VRAM/RAM between calls. This is especially useful when running multiple models or when GPU memory is limited. The trade-off is higher first-token latency on subsequent calls due to model reload.

1. Install:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
2. Pull models:
   ```bash
   ollama pull llama3.1:8b
   ollama pull qwen3-vl:8b
   ```
3. Run the daemon:
   ```bash
   ollama serve
   ```
4. Verify:
   ```bash
   lsof -i :11434          # confirm service
   ollama list             # confirm models
   ollama run llama3.1:8b  # optional smoke test
   ```

### OpenAI

Set `OPENAI_API_KEY` in `.env` (or export it in your shell). LiteLLM automatically reads it.

---

## 5. Run the Stack

```bash
# API (preferred)
uv run llumdocs-api
# or: uv run uvicorn llumdocs.api.app:app --reload

# Gradio UI (preferred)
uv run llumdocs-ui
# or: uv run python -m llumdocs.ui.main
```

Visit `http://localhost:8000/docs` for the FastAPI explorer and `http://localhost:7860` for the UI (default Gradio port).

---

## 6. Example LiteLLM Scripts (optional)

The `setup/` folder contains two sample scripts that demonstrate raw LiteLLM usage:

- `setup/example_litellm.py` – CLI examples for Ollama + OpenAI.
- `setup/example_litellm_gradio.py` – small Gradio playground that lists models via LiteLLM.

Run them after following the steps above:

```bash
uv run python setup/example_litellm.py
uv run python setup/example_litellm_gradio.py
```

They are helpful when validating that your providers and credentials are correctly wired before touching the main app.

---

## Troubleshooting

- **`uv sync` fails on Linux** – ensure you have build tools (`build-essential`, `python3.12-dev`) installed.
- **Ollama models missing** – rerun `ollama list`; if empty, the pull may have failed. Check connectivity or disk space.
- **API cannot resolve model** – confirm `LLUMDOCS_DEFAULT_MODEL` matches one of the LiteLLM identifiers listed in the [LiteLLM docs](https://docs.litellm.ai/).

---

## 7. Docker Deployment (Optional)

LlumDocs can be deployed using Docker and Docker Compose profiles, with optional Ollama and Hugging Face integration.

### Quick Start with Docker Compose (CPU + UI)

1. **Create a `.env` file** in the project root with your configuration:
   ```bash
   OPENAI_API_KEY=sk-your-key
   LLUMDOCS_DEFAULT_MODEL=gpt-4o-mini
   LLUMDOCS_DEFAULT_VISION_MODEL=o4-mini
   ```

2. **Build and start services (API + UI + Ollama, CPU-only):**
   ```bash
   cd docker
   docker compose --profile cpu --profile ui up --build
   ```

3. **Access services:**
   - FastAPI: `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`
   - Gradio UI: `http://localhost:7860`
   - Ollama (Docker): `http://localhost:11435` (mapped to `ollama:11434` in the network)

For GPU profiles, pre-bundled Hugging Face models, and more advanced options, see `docker/README.md`. Once the above steps succeed, continue with `docs/TESTING.md` to validate your setup via unit and integration tests.

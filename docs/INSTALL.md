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

# Create the virtualenv and install deps
uv sync
source .venv/bin/activate            # Windows: .venv\Scripts\activate
```

`uv sync` reads `pyproject.toml`, creates `.venv`, and installs both runtime dependencies and optional dev extras when you pass `--all-extras`.

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

Key variables understood by `llumdocs.llm.resolve_model()`:

- `OPENAI_API_KEY` – enables OpenAI routing through LiteLLM.
- `LLUMDOCS_DEFAULT_MODEL` – preferred text model (see recommended models below).
- `LLUMDOCS_DEFAULT_VISION_MODEL` – model for image description tasks (see recommended models below).
- `LLUMDOCS_DISABLE_OLLAMA=1` – opt-out of Ollama even if installed.
- `OLLAMA_API_BASE` – change the Ollama host (default `http://localhost:11434`).
- `OLLAMA_KEEP_ALIVE` – server-side default keep_alive (informational only; client requests explicitly set `keep_alive=0` to unload models immediately after inference).
- `LLUMDOCS_LLM_TIMEOUT_SECONDS` – timeout for text LLM calls in seconds (default: 30.0).
- `LLUMDOCS_VISION_TIMEOUT_SECONDS` – timeout for vision/image models (default: 60.0, but falls back to `LLUMDOCS_LLM_TIMEOUT_SECONDS` when set).
- `LLUMDOCS_ENABLE_EMAIL_INTELLIGENCE` – set to `0` to disable email intelligence (default: `1`).
- `LLUMDOCS_EMAIL_MAX_TOKENS` – max tokens per email fed to Hugging Face pipelines (default: 512).
- `LLUMDOCS_MAX_IMAGE_SIZE_BYTES` – maximum image upload size in bytes (default: 10MB).
- `HF_HOME` – Hugging Face cache directory (for email intelligence models).

**Recommended models:**

| Use case     | Recommended model ids        |
|--------------|------------------------------|
| Text tools   | `gpt-4o-mini` or `ollama/llama3.1:8b` |
| Vision tools | `o4-mini` or `ollama/qwen3-vl:8b` |

Example:

```ini
OPENAI_API_KEY=sk-your-key
LLUMDOCS_DEFAULT_MODEL=gpt-4o-mini
LLUMDOCS_DEFAULT_VISION_MODEL=o4-mini
OLLAMA_API_BASE=http://localhost:11434
LLUMDOCS_LLM_TIMEOUT_SECONDS=30.0
LLUMDOCS_VISION_TIMEOUT_SECONDS=60.0
LLUMDOCS_ENABLE_EMAIL_INTELLIGENCE=1
LLUMDOCS_EMAIL_MAX_TOKENS=512
HF_HOME=/models/hf
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
# API
uv run uvicorn llumdocs.api.app:app --reload

# Gradio UI
uv run python -m llumdocs.ui.main
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

LlumDocs can be deployed using Docker and Docker Compose, with optional Ollama integration.

### Quick Start with Docker Compose

1. **Create a `.env` file** in the project root with your configuration:
   ```bash
   OPENAI_API_KEY=sk-your-key
   LLUMDOCS_DEFAULT_MODEL=gpt-4o-mini
   LLUMDOCS_DEFAULT_VISION_MODEL=o4-mini
   INSTALL_EMAIL=1  # Set to 1 to include email intelligence dependencies
   ```

2. **Build and start services:**
   ```bash
   docker-compose up -d
   ```

3. **Pre-pull Ollama models** (if using Ollama):
   ```bash
   docker-compose exec ollama ollama pull llama3.1:8b
   docker-compose exec ollama ollama pull qwen3-vl:8b
   ```

4. **Access services:**
   - FastAPI: `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`
   - Ollama: `http://localhost:11434`

### Dockerfile Details

The `Dockerfile` supports building with or without email intelligence:

```bash
# Build without email intelligence (lighter image)
docker build -t llumdocs .

# Build with email intelligence
docker build --build-arg INSTALL_EMAIL=1 -t llumdocs .
```

### Production Considerations

For production deployments, consider:

- **Uvicorn workers**: Run multiple workers for better concurrency:
  ```bash
  uvicorn llumdocs.api.app:app --host 0.0.0.0 --port 8000 --workers 4
  ```

- **Resource limits**: Set appropriate CPU/memory limits in `docker-compose.yml` or Kubernetes manifests.

- **Health checks**: The container includes a health check endpoint at `/health` and readiness at `/ready`.

- **Persistent volumes**:
  - HF models cache: `/models/hf` (mounted as `hf-cache` volume)
  - Ollama models: `/root/.ollama` (mounted as `ollama-models` volume)

- **GPU support**: For GPU-accelerated Ollama, uncomment the GPU deployment section in `docker-compose.yml` and ensure NVIDIA Container Toolkit is installed.

---

Once the above steps succeed, continue with `docs/TESTING.md` to validate your setup via unit and integration tests.

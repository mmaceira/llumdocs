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

### Heavy Dependencies Note

LlumDocs includes `torch` and `transformers` as core dependencies to support the **email intelligence** feature (routing, phishing detection, sentiment analysis). These packages are large (~2-3 GB) and require significant disk space and memory.

- **Email intelligence** will gracefully degrade if `torch` is missing, but the feature will be unavailable.
- If you don't need email intelligence and want a lighter installation, you can:
  - Remove `torch` and `transformers` from `pyproject.toml` dependencies (they're only used by `llumdocs/services/email_intelligence_service.py`)
  - Or create an optional extra that excludes them for constrained environments

For most use cases (translation, summaries, keywords, image descriptions), these heavy dependencies are not required.

### Optional: Email intelligence models (Hugging Face)

The email intelligence service depends on **`torch`** and **`transformers`** to load
three Hugging Face pipelines:

- Zero-shot routing: `MoritzLaurer/bge-m3-zeroshot-v2.0`
- Phishing detection: `cybersectony/phishing-email-detection-distilbert_v2.1`
- Sentiment: `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`

These can be overridden via environment variables:

```bash
export LLUMDOCS_EMAIL_ZEROSHOT_MODEL="your-org/your-zeroshot-model"
export LLUMDOCS_EMAIL_PHISHING_MODEL="your-org/your-phishing-model"
export LLUMDOCS_EMAIL_SENTIMENT_MODEL="your-org/your-sentiment-model"
```

The first call to each capability will be slower (model download + load). Subsequent
calls reuse the cached pipeline. In constrained environments you may choose not to
use this module at all.

---

## 3. Environment Variables

Copy the template, then edit values as needed:

```bash
cp .env.template .env
```

Key variables understood by `llumdocs.llm.resolve_model()`:

- `OPENAI_API_KEY` – enables OpenAI routing through LiteLLM.
- `LLUMDOCS_DEFAULT_MODEL` – preferred text model (`gpt-4o-mini`, `ollama/llama3.1:8b`, etc.).
- `LLUMDOCS_DEFAULT_VISION_MODEL` – model for image description tasks.
- `LLUMDOCS_DISABLE_OLLAMA=1` – opt-out of Ollama even if installed.
- `OLLAMA_API_BASE` – change the Ollama host (default `http://localhost:11434`).

Example:

```ini
OPENAI_API_KEY=sk-your-key
LLUMDOCS_DEFAULT_MODEL=ollama/llama3.1:8b
LLUMDOCS_DEFAULT_VISION_MODEL=ollama/qwen3-vl:8b
OLLAMA_API_BASE=http://localhost:11434
```

---

## 4. Configure LiteLLM Providers

### Ollama

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

Once the above steps succeed, continue with `docs/TESTING.md` to validate your setup via unit and integration tests.

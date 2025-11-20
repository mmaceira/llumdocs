 # Testing LlumDocs

This document describes how to run the automated suites after you install the project (see `docs/INSTALL.md`). Tests assume the repository root as working directory.

---

## Unit Tests (mocked LLM calls)

No external providers are required—LiteLLM calls are mocked.

To avoid pulling Hugging Face models during tests, run the unit suite without
any email-intelligence integration tests (currently, there are none that require
HF; if you add some, mark them `@pytest.mark.integration`).

```bash
# run everything
uv run pytest

# skip integration markers
uv run pytest -m "not integration"

# unit-only, no HuggingFace (excludes email intelligence tests)
# Useful for CI jobs without GPU or when transformers/torch are not installed
uv run pytest -m "not integration" --ignore=tests/test_email_intelligence_service.py

# single file
uv run pytest tests/test_translation_service.py
```

---

## Integration Tests (live providers)

These tests exercise real OpenAI/Ollama models and are marked with `@pytest.mark.integration`.

### 1. Configure providers

- **OpenAI**
  ```bash
  export OPENAI_API_KEY="pk-live-key"
  ```

- **Ollama**
  ```bash
  ollama serve
  ollama pull llama3.1:8b
  ollama pull qwen3-vl:8b
  ```

### 2. Specify test models

```bash
export LLUMDOCS_LIVE_TEST_MODELS="gpt-4o-mini,ollama/llama3.1:8b"
export LLUMDOCS_LIVE_TEST_VISION_MODELS="o4-mini,ollama/qwen3-vl:8b"
```

If the variables are omitted, integration tests are automatically skipped.

### 3. Run the suite

```bash
# all integration tests
uv run pytest tests/integration -m integration

# individual files
uv run pytest tests/integration/test_text_tools_live.py -m integration
uv run pytest tests/integration/test_translation_live.py -m integration
uv run pytest tests/integration/test_image_description_live.py -m integration
```

### Model naming cheatsheet

- Ollama text: `ollama/llama3.1:8b`
- Ollama vision: `ollama/qwen3-vl:8b`
- OpenAI: `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`, `o4-mini`, etc.

---

## Troubleshooting

- **`pytest` hangs** – ensure no integration test is waiting for remote providers; run with `-m "not integration"` to confirm unit suite is clean.
- **`llm.resolve_model` errors** – double-check `LLUMDOCS_LIVE_TEST_MODELS` so every entry matches a LiteLLM identifier.
- **Skipping unexpectedly** – `pytest` shows “SKIPPED” when env vars are missing. Export them in the same shell before running.

Once both suites pass you can be confident that API endpoints, services, and LiteLLM wiring are behaving as expected.

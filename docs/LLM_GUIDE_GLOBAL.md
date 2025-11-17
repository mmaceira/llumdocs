# Global Guide for LLM Developers of LlumDocs

> **This document is intended as a "system prompt" or base guide for any LLM**
> that generates code or configuration for the **LlumDocs** project.

---

## 1. Role and objective

You are a **Python development assistant** working within the **LlumDocs** project.

Your objective is:

1. Implement features using:
   - **Python 3.x**
   - **LiteLLM** as a proxy/SDK for language and vision models.
   - **Gradio** for the graphical interface.
   - **FastAPI** (or similar) for the REST API.
2. Maintain code that is:
   - modular
   - testable
   - easily reusable for both **UI** and **API**.

---

## 2. Technical stack

### 2.1. Language and ecosystem

- **Python 3.11+** (or appropriate version for uv and modern libraries).
- Environment and dependency manager: **`uv`** (virtual environments and fast installation).
- Code style:
  - **ruff** for linting and some formatting.
  - **black** for code formatting.
  - `pre-commit` to apply them automatically.

### 2.2. Models and inference: LiteLLM

- [LiteLLM](https://github.com/BerriAI/litellm) is used as an abstraction layer.
- From the code, **OpenAI style** is always used:
  - `chat/completions`
  - `model="gpt-4o-mini"` (or others)
- LiteLLM can:
  - Act as a proxy to OpenAI.
  - Connect with Ollama and other providers.
- All LLM/VLM call logic must be centralized in one file:
  - `llumdocs/app/litellm_client.py`.

### 2.3. Frontend: Gradio

- UI in **Gradio**:
  - initial screen with utility selector.
  - within each utility, **a single action button**.
- The UI must be a **very thin layer** that:
  - collects user inputs.
  - calls functions from `services/`.
  - shows results without complex logic.

### 2.4. REST API

- API implemented with **FastAPI** (or equivalent).
- Exposes endpoints such as:
  - `POST /api/translate`
  - `POST /api/text/plain`
  - `POST /api/invoices/extract`
  - `POST /api/documents/summarize`
  - `POST /api/search`
- All endpoints must delegate logic to `services/`.

---

## 3. Project organization

We assume the base structure:

```text
llumdocs/
  app/
    __init__.py
    config.py
    litellm_client.py
    models/
    services/
    ui/
    api/
  tests/
  docs/
```

### 3.1. `litellm_client.py`

This module must:

- Load configuration (default model, timeout, etc.).
- Provide functions such as:

```python
from typing import List, Dict, Any

def chat_completion(messages: List[Dict[str, str]], model: str | None = None, **kwargs: Any) -> str:
    """Send a chat prompt to the configured model via LiteLLM and return only the response text."""
    ...

def vision_completion(
    prompt: str,
    image_bytes: bytes,
    model: str | None = None,
    **kwargs: Any,
) -> str:
    """Make a call to a multimodal model to describe an image."""
    ...
```

- Must not include business logic (only call abstraction).

### 3.2. `services/`

Each main utility must have **a dedicated module**. Examples:

- `translation_service.py`
- `technical_text_service.py`
- `plain_language_service.py`
- `summarization_service.py`
- `keyword_service.py`
- `invoice_extraction_service.py`
- `image_description_service.py`
- `classification_service.py`
- `repository_service.py`
- `search_service.py`

Each module must offer clear functions, e.g.:

```python
def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    ...

def simplify_text(text: str, target_reading_level: str | None = None) -> str:
    ...
```

### 3.3. `ui/`

- Gradio components for each utility.
- A `main_gradio.py` that mounts the application with tabs or menus.

### 3.4. `api/`

- Main file `main_api.py` with FastAPI application creation.
- Grouped endpoint files (`translation_endpoints.py`, etc.).
- Pydantic models must be used for request/response.

---

## 4. Implementation principles

1. **Separation of concerns**
   - UI (Gradio) ≠ Logic (services) ≠ Infrastructure (litellm_client, config).
   - REST API is only "glue" between the HTTP world and services.

2. **Testable services**
   - Must receive simple arguments (strings, dicts, Pydantic models).
   - Must not depend directly on Gradio or FastAPI.
   - LLM calls can be injected or simulated in tests.

3. **Disciplined use of LiteLLM**
   - Do not make "direct OpenAI" calls from services.
   - Everything must go through `litellm_client`.

4. **Code style and quality**
   - Types (type hints) in public functions.
   - Brief but descriptive docstrings.
   - Respect `ruff` + `black` + conventions defined in the project.

5. **Clarity of I/O**
   - Each service must clearly specify:
     - input parameters
     - output structure (dict or Pydantic model).
   - Avoid "magic responses" with different formats depending on the case.

---

## 5. Typical tasks for this LLM

When you are asked to implement or modify some part of LlumDocs, it is usually for:

- Creating a new **service module** (e.g. `classification_service.py`).
- Adding a new **UI component** (e.g. `classification_ui.py`).
- Defining a new **FastAPI endpoint**.
- Writing **tests** for some service.
- Adjusting **prompts** or LiteLLM calls.

In all cases:

- Review that what you generate fits with:
  - the general design
  - the code style
  - the reuse philosophy.

---

## 6. Security and privacy considerations

- Do not write or log **API keys** in code.
- Do not include sensitive document content in logs.
- If logging is needed, do it with:
  - document identifiers
  - text length
  - timestamps
  - operation type
- Prepare code to be able to:
  - disable verbose logs in production environments.

---

## 7. Prompt best practices

When defining prompts for services (translation, summaries, etc.):

- Be **explicit** about the output format (e.g. "return only JSON").
- Avoid ambiguous instructions.
- For extractions, prefer:
  - specifying a clear JSON schema.
  - asking the model to validate formats (dates, numbers, etc.) when it makes sense.
- For summaries and simplifications, emphasize:
  - "do not add information that is not in the original text".

---

## 8. Examples of LiteLLM call patterns

### 8.1. Basic chat completions

```python
from llumdocs.app.litellm_client import chat_completion

def summarize_document(text: str, summary_type: str = "short") -> str:
    system_msg = {
        "role": "system",
        "content": (
            "You are an assistant that summarizes documents in English. "
            "Do not invent information."
        ),
    }
    user_msg = {
        "role": "user",
        "content": f"Summary type: {summary_type}\n\nText:\n{text}",
    }
    return chat_completion(messages=[system_msg, user_msg], model="gpt-4o-mini")
```

### 8.2. Structured extraction (JSON)

```python
def extract_invoice_fields(text: str) -> dict:
    system_msg = {
        "role": "system",
        "content": (
            "You are an invoice data extractor. "
            "Return exactly a JSON with the following fields: "
            "invoice_number, date, supplier_name, supplier_vat, total_amount, currency."
        ),
    }
    user_msg = {"role": "user", "content": text}
    raw = chat_completion(
        messages=[system_msg, user_msg],
        model="gpt-4o-mini",
        temperature=0,
    )
    # parse JSON with json.loads, etc.
    ...
```

---

## 9. Conclusion

This global guide serves as a **reference framework** for any LLM working on the LlumDocs project.

When generating code:

- Assume the `llumdocs/app/...` structure.
- Follow the principles of layer separation.
- Centralize model usage through LiteLLM.
- Respect the style and configuration defined in development files (ruff, pre-commit, etc.).

The final objective is to build a project that is:

- **clean**, **coherent** and **extensible**,
- in which adding new utilities is natural and safe.

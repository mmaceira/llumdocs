# LlumDocs

**LlumDocs** is a platform to understand, transform and manage documents and multimedia content, designed for SMEs and organizations that want to leverage generative AI without technical complexity.

The name _LlumDocs_ reflects the idea of shedding **light** on documents and complex information, making them more understandable, exploitable and easily integrable within existing workflows.

---

## Main features

LlumDocs offers a series of utilities accessible both via **graphical interface (Gradio)** and via **REST API**:

- **Translate texts** between languages.
- **Make texts more technical** (increase formality / technicality).
- **Make texts more understandable** for all audiences (plain language).
- **Extract structured information from documents** (e.g. invoices).
- **Describe images** (captioning and detailed descriptions).
- **Summarize documents** (short, long, executive).
- **Extract keywords** from documents.
- **Sort and classify documents** (by theme, type, etc.).
- **Document repository manager** (internal mini data lake).
- **Search engine**:
  - Keyword search (basic full-text).
  - Semantic search (embeddings).
  - Hybrid search (words + semantic similarity).

The objective is to have **a single tool** that concentrates the most common operations on text, documents and images, without having to set up multiple dispersed services.

---

## Basic architecture

### AI Backend: LiteLLM as abstraction layer

- [LiteLLM](https://github.com/BerriAI/litellm) is used as a **proxy and SDK** over different models.
- From LlumDocs' point of view, **OpenAI-style is always used**:
  - `POST /v1/chat/completions`
  - `model="gpt-4o-mini"` (or equivalents)
  - interfaces of type `messages=[...]`.
- LiteLLM can:
  - Route requests to **OpenAI** (or other SaaS).
  - Route requests to **local models via Ollama**.
- Routing logic (which model is used when) is controlled via LiteLLM configuration, not from business logic.

### Frontend: Gradio

- Frontend implemented with **Gradio**.
- There is an **initial screen** where the user selects the utility:
  - Translation
  - Technical text
  - Plain language
  - Summaries
  - Invoice extraction
  - Keywords
  - Image description
  - Classification / sorting
  - Repository search
- Within each utility:
  - **Very simple** interface:
    - Minimal inputs (text, file, selector).
    - **A single main action button** (e.g. "Translate", "Summarize", "Extract data").

### REST API

In addition to Gradio, LlumDocs exposes a **REST API** (e.g. based on FastAPI) that allows:

- Sending texts or documents (upload).
- Requesting operations:
  - translation
  - summary
  - structured extraction
  - repository search
- Receiving results as **structured JSON**.

This facilitates integrating LlumDocs with:

- ERP / CRM
- RPA / workflow orchestrators (n8n, Airflow, etc.)
- Internal applications.

---

## Code organization

The objective is for all LlumDocs implementation to live in a **self-contained folder** within the repository (e.g. a monorepo), with the following suggested structure:

```text
llumdocs/
  app/
    __init__.py
    config.py
    litellm_client.py

    models/
      __init__.py
      invoices.py
      search.py
      text_ops.py

    services/
      __init__.py
      translation_service.py
      technical_text_service.py
      plain_language_service.py
      summarization_service.py
      keyword_service.py
      invoice_extraction_service.py
      image_description_service.py
      classification_service.py
      repository_service.py
      search_service.py

    ui/
      __init__.py
      main_gradio.py
      translation_ui.py
      technical_text_ui.py
      plain_language_ui.py
      summarization_ui.py
      keyword_ui.py
      invoice_ui.py
      image_ui.py
      classification_ui.py
      search_ui.py

    api/
      __init__.py
      main_api.py
      translation_endpoints.py
      summarization_endpoints.py
      ...
  tests/
    test_translation_service.py
    test_summarization_service.py
    ...

  docs/
    README_LlumDocs.md
    LLM_GUIDE_GLOBAL.md
    LLM_FEATURE_SPECS.md
    LLM_DEVELOPMENT_GUIDE.md
```

Key points:

- **`services/`** contains reusable business logic.
- **`ui/`** is a thin layer that calls services.
- **`api/`** is another thin layer over the same services.
- **`models/`** defines data schemas (Pydantic, etc.).
- **`litellm_client.py`** encapsulates all LLM / VLM model calls.

---

## Design objectives

1. **Functional clarity**
   The app must be easy to understand:
   - each utility has a clear service
   - each service has well-defined UI and endpoints.

2. **Code reuse**
   Do not duplicate logic between UI and API:
   - services in `services/` must be able to be tested without Gradio or FastAPI.

3. **Extensibility**
   Adding a new utility should be:
   - create a new module in `services/`
   - optionally add a UI file + endpoints.

4. **Provider independence**
   Thanks to LiteLLM, you can change providers (OpenAI, Azure OpenAI, Ollama, etc.) without having to touch service code:
   - only LiteLLM configuration and environment variables are changed.

---

## Typical usage flows

### Example 1: Quick translation via UI

1. User opens the Gradio UI.
2. Selects the **"Translate texts"** utility.
3. Pastes text into the input field, chooses source/target language.
4. Clicks the **"Translate"** button.
5. UI calls the service `translation_service.translate_text(...)`.
6. Service makes one or more calls via `litellm_client.chat_completion(...)`.
7. UI shows the result.

### Example 2: Invoice data extraction via API

1. Another internal system makes a `POST /api/invoices/extract` with a PDF.
2. Endpoint saves the file temporarily.
3. Passes the document through OCR pipeline (external, encapsulated in a service function).
4. Calls the model via LiteLLM to return a JSON with invoice fields.
5. API returns structured JSON to the client.

### Example 3: Semantic search in repository

1. User writes a text query in the search UI.
2. The **search + embeddings** service generates embeddings of the query.
3. Searches are performed:
   - by keyword (text search)
   - by embedding similarity.
4. Results are combined and sorted.
5. Most relevant documents are shown, with snippet and link.

---

## Approximate roadmap

1. **MVP 0.1**
   - Translation
   - Technical text
   - Plain language
   - Summaries
   - LiteLLM integration
   - Basic Gradio UI
   - Basic API for 2–3 features

2. **Version 0.2**
   - Invoice extraction
   - Keywords
   - Image description
   - Minimal document repository manager (files + metadata)

3. **Version 0.3**
   - Complete search engine (keyword + semantic + embeddings)
   - Document classification / sorting
   - Security improvements, logs, basic RBAC

4. **Version 1.0**
   - Complete documentation
   - Basic test suite
   - Deployment pipeline (Docker, etc.)
   - Cost optimizations (cache, batching, etc.)

---

LlumDocs is born as a core on which a complete ecosystem of AI-based document productivity can be built, maintaining a balance between ease of use and technical power.

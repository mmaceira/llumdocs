# Feature Specifications for LLMs (LlumDocs)

This document describes, for each LlumDocs utility:

- Functional objective
- Inputs / outputs
- Technical requirements
- Implementation guides for:
  - service (`services/`)
  - Gradio UI (`ui/`)
  - API endpoint (`api/`)

---

## 1. Text translation

### Objective

Translate texts between languages using language models via LiteLLM, maintaining meaning and general tone.

### Inputs

- `text: str` – original text.
- `source_lang: str` – source language code (e.g. `"ca"`, `"es"`, `"en"`), or `"auto"` if we want automatic detection.
- `target_lang: str` – target language code.

### Outputs

- `translated_text: str` – translated text.
- (Optional) `meta: dict`:
  - `detected_source_lang`
  - `model_used`
  - etc.

### Service: `translation_service.py`

Recommended API:

```python
def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text from one language to another using LiteLLM."""
    ...
```

- Must prepare a clear prompt:
  - indicate source/target language
  - request that it returns only the translated text, without explanations.
- Must call `litellm_client.chat_completion(...)`.

### UI: `translation_ui.py`

- Components:
  - Large `gr.Textbox` for original text.
  - `gr.Dropdown` for `source_lang` (with `"auto"` option).
  - `gr.Dropdown` for `target_lang`.
  - `gr.Button("Translate")`.
  - Output `gr.Textbox`.

### API: `translation_endpoints.py`

Suggested endpoint:

```http
POST /api/translate
Content-Type: application/json

{
  "text": "Hello world",
  "source_lang": "en",
  "target_lang": "ca"
}
```

Response:

```json
{
  "translated_text": "Hola món"
}
```

---

## 2. Making texts more technical

### Objective

Provide a more technical / formal version of a text, optionally indicating a **domain** (medical, legal, technological, etc.) and a **level**.

### Inputs

- `text: str`
- `domain: str | None` – e.g. `"generic"`, `"tech"`, `"medical"`, `"legal"`.
- `target_level: str | None` – e.g. `"intermediate"`, `"advanced"`, `"expert"`.

### Outputs

- `technical_text: str` – more technical version of the text.

### Service: `technical_text_service.py`

```python
def make_text_more_technical(
    text: str,
    domain: str | None = None,
    target_level: str | None = None,
) -> str:
    ...
```

- The prompt must:
  - request formal register.
  - incorporate domain vocabulary if provided.
  - maintain original meaning.
  - not add new information.

### UI

- Input text.
- Dropdown for `domain`.
- Dropdown or `Radio` for `target_level`.
- Button "Make more technical".
- Output text.

### API

`POST /api/text/technical`

Body:

```json
{
  "text": "...",
  "domain": "tech",
  "target_level": "expert"
}
```

---

## 3. Making texts more understandable (plain language)

### Objective

Transform a complex text into a clear and accessible version for general audiences or for a specific level (children, teenagers, adults).

### Inputs

- `text: str`
- `target_reading_level: str | None` – e.g. `"child"`, `"teen"`, `"adult_general"`.

### Outputs

- `plain_text: str` – simplified text.

### Service: `plain_language_service.py`

```python
def simplify_text(
    text: str,
    target_reading_level: str | None = None,
) -> str:
    ...
```

- The prompt must:
  - request short sentences.
  - avoid technical terms.
  - explain difficult concepts with simple examples.
  - **not modify the meaning**.

### UI

- Input text.
- Level selector.
- Button "Make more understandable".
- Output text.

### API

`POST /api/text/plain`

---

## 4. Structured data extraction from invoices

### Objective

Read an invoice (PDF, image or text) and return structured data such as:

- `invoice_number`
- `date`
- `supplier_name`
- `supplier_vat`
- `total_amount`
- `currency`
- `line_items` (detail lines)

### Inputs

- `file`: uploaded file (PDF/image) or already extracted text.
- `schema_name: str | None` – e.g. `"invoice_basic"` to choose the extraction schema.

### Outputs

- `data: dict` – structured JSON according to the schema.
- (Optional) `raw_text: str` – OCR text.

### Service: `invoice_extraction_service.py`

Responsibilities:

1. If input is a file:
   - Pass it through an OCR layer (future: Docling, Azure Document Intelligence, etc.).
2. Normalize the text (remove strange characters, etc.).
3. Call LiteLLM with an extraction prompt:
   - describe the expected JSON schema.
   - emphasize that it must be valid JSON.
4. Parse and validate JSON with Pydantic models (e.g. `InvoiceModel` in `models/invoices.py`).

### UI

- File upload.
- Button "Extract data".
- Visualization:
  - Formatted JSON.
  - Key fields (supplier, total amount, date) in a table.

### API

`POST /api/invoices/extract`

Multipart request (file) or JSON if text is already sent.

---

## 5. Image description

### Objective

Provide a textual description of an image, with controllable levels of detail.

### Inputs

- `image`: image file.
- `detail_level: str` – `"short"` or `"detailed"`.

### Outputs

- `description: str` – generated description.

### Service: `image_description_service.py`

```python
def describe_image(image_bytes: bytes, detail_level: str = "short") -> str:
    ...
```

- Must make a call to a multimodal model via LiteLLM.
- Prompt:
  - "Describe this image in English"
  - if `detail_level == "detailed"`, add more context, secondary objects, relationships.

### UI

- Image upload.
- Detail level selector.
- Button "Describe image".
- Output text.

### API

`POST /api/images/describe`

---

## 6. Document summaries

### Objective

Create summaries of documents (text or file) in different formats:

- short
- detailed
- executive (for executives)

### Inputs

- `text: str` or `file`.
- `summary_type: str` – `"short"`, `"detailed"`, `"executive"`.

### Outputs

- `summary: str` – generated summary.

### Service: `summarization_service.py`

```python
def summarize_document(text: str, summary_type: str = "short") -> str:
    ...
```

- Prompt:
  - For `"short"`: 3–5 sentences maximum.
  - For `"detailed"`: more extensive, can be in sections.
  - For `"executive"`: oriented to decision-makers, key points, risks and recommendations.

### UI

- Text or file input.
- `summary_type` selector.
- Button "Summarize".
- Result.

### API

`POST /api/documents/summarize`

---

## 7. Keyword extraction

### Objective

Extract relevant keywords or phrases from a text, to facilitate indexing and search.

### Inputs

- `text: str`
- `max_keywords: int` – maximum number of keywords to return (e.g. 5–20).

### Outputs

- `keywords: list[str]`
- (Optional) `scores: list[float]` – relevance score.

### Service: `keyword_service.py`

```python
def extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
    ...
```

- Prompt:
  - Explicitly request a **list** of words/phrases.
  - Prohibit explanations.
- Optionally can combine:
  - TF-IDF heuristics
  - with LLM refinement.

### UI

- Input text.
- Slider for `max_keywords`.
- Button "Extract keywords".
- Results list.

### API

`POST /api/text/keywords`

---

## 8. Sorting and classifying documents

### Objective

Classify documents (texts or files) into categories and sort them by relevance or similarity.

### Inputs

- `documents: list[str]` or document identifiers in the repository.
- `labels: list[str]` – available categories (`"invoice"`, `"contract"`, `"report"`, etc.).

### Outputs

- For each document:
  - `category: str`
  - `confidence: float` (0–1)
- Possibly a recommended order.

### Service: `classification_service.py`

```python
from dataclasses import dataclass

@dataclass
class ClassificationResult:
    document_id: str
    category: str
    confidence: float

def classify_documents(docs: list[str], labels: list[str]) -> list[ClassificationResult]:
    ...
```

- Can be implemented:
  - directly with LLM (prompt "classify into these categories").
  - or with embeddings + nearest neighbour (when there are labeled examples).

### UI

- Multiple upload or textarea with multiple texts.
- Fields to indicate labels (e.g. `gr.Textbox` with list separated by commas).
- Button "Classify".
- Results table.

### API

`POST /api/documents/classify`

---

## 9. Document repository manager

### Objective

Maintain an internal repository of documents and metadata for:

- saving extraction results
- performing subsequent searches
- having traceability

### Basic inputs (save):

- `content: str` – document text.
- `metadata: dict` – e.g.:
  - `source_type` (`"upload"`, `"email"`, etc.)
  - `doc_type` (`"invoice"`, `"contract"`, etc.)
  - `created_at`, `tags`, etc.

### Outputs

- `document_id: str` – internal identifier.
- Possibility to retrieve complete document.

### Service: `repository_service.py`

Must manage:

- Storage (to start, can be file + a small JSON index or SQLite).
- Operations:
  - `save_document(content, metadata) -> document_id`
  - `get_document(document_id) -> Document`
  - `list_documents(filters) -> list[DocumentSummary]`

---

## 10. Search engine (keyword, semantic, embeddings)

### Objective

Allow searching within the repository with different modes:

- **keyword** – direct textual search.
- **semantic** – similarity by embeddings.
- **hybrid** – combination of both.

### Inputs

- `query_text: str`
- `mode: str` – `"keyword"`, `"semantic"`, `"hybrid"`.
- `filters: dict | None` – e.g. document type, dates, etc.

### Outputs

- List of results:
  - `document_id`
  - `title` (or snippet)
  - `score`
  - `metadata`

### Service: `search_service.py`

Recommended functions:

```python
def search_documents(
    query_text: str,
    mode: str = "hybrid",
    filters: dict | None = None,
) -> list[dict]:
    ...
```

- Mode `"keyword"`: e.g. simple TF-IDF or a lightweight library.
- Mode `"semantic"`:
  - embedding generation with LiteLLM for:
    - documents (precomputed).
    - query (real-time).
  - cosine similarity.
- Mode `"hybrid"`:
  - combine keyword and semantic scores.

### UI

- Search box (`gr.Textbox`).
- Dropdown for `mode`.
- Optionally simple filters (document type).
- Button "Search".
- Results in list/table form.

### API

`POST /api/search`

Body:

```json
{
  "query_text": "March invoices",
  "mode": "hybrid",
  "filters": {"doc_type": "invoice"}
}
```

---

This document should be used together with the **Global Guide (`LLM_GUIDE_GLOBAL.md`)** to ensure that generated code is consistent with the architecture and general style of LlumDocs.

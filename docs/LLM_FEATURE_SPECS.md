# Feature Specifications for LlumDocs

Each section below describes what a capability does, how users interact with it, and the minimum contracts every layer (service, API, UI) must honor. Use this together with `docs/LLM_GUIDE_GLOBAL.md` when building new functionality.

---

## Legend

- ✅ Shipping today (wired in both API and Gradio)
- ⚙️ Exists as service logic but not fully surfaced yet
- 🚧 Planned / design complete, waiting for build

---

## 1. Text Translation — ✅

- **Goal:** Translate between Catalan, Spanish, English with optional auto-detect.
- **Inputs:** `text`, `source_lang` (`"auto"` allowed), `target_lang`.
- **Outputs:** `translated_text`, optional `meta` (`detected_source_lang`, `model_used`).
- **Service:** `translation_service.translate_text(text, source_lang, target_lang)`.
- **Prompt notes:** force target language, keep tone, no explanations.
- **API:** `POST /api/translate` (`translation_endpoints.py` models).
- **UI:** Gradio tab with textarea, source/target dropdowns (source includes `"auto"`), single translate button.

---

## 2. Technical Rewrite — ✅

- **Goal:** Raise formality/technicality for a text, optionally scoped to a domain or level.
- **Inputs:** `text`, optional `domain`, optional `target_level`.
- **Outputs:** `technical_text`.
- **Service:** `llumdocs.services.text_transform_service.make_text_more_technical(...)`.
- **Prompt notes:** mention domain vocabulary, forbid hallucinations, keep structure.
- **API:** `POST /api/text/technical`.
- **UI:** Textbox + dropdowns for domain and level, single action button.

---

## 3. Plain Language Rewrite — ✅

- **Goal:** Simplify text for general or specific audiences (child/teen/adult).
- **Inputs:** `text`, optional `target_reading_level`.
- **Outputs:** `plain_text`.
- **Service:** `llumdocs.services.text_transform_service.simplify_text(...)`.
- **Prompt notes:** short sentences, simple vocabulary, no loss of meaning, can give analogies.
- **API:** `POST /api/text/plain`.
- **UI:** Textbox + reading-level selector + button.

---

## 4. Document Summaries — ✅

- **Goal:** Produce short, detailed, or executive summaries for pasted text or uploaded files (after OCR).
- **Inputs:** `text` or extracted file text, `summary_type`.
- **Outputs:** `summary`.
- **Service:** `llumdocs.services.text_transform_service.summarize_document(...)`.
- **Prompt notes:** set constraints per summary type (sentences count, highlight risks).
- **API:** `POST /api/documents/summarize`.
- **UI:** Text/file input, summary-type dropdown, button, result area.

---

## 5. Keyword Extraction — ✅

- **Goal:** Return the top N keywords/phrases for indexing and metadata.
- **Inputs:** `text`, `max_keywords`.
- **Outputs:** `keywords` (list), optional `scores`.
- **Service:** `llumdocs.services.text_transform_service.extract_keywords(...)`.
- **Prompt notes:** ask for JSON array, disallow commentary, mention max length. The service will try to coerce bullet/numbered lists when JSON decoding fails, but models that cannot reliably emit list-like output should be avoided or prompt-tuned.
- **API:** `POST /api/text/keywords`.
- **UI:** Textbox + slider for keyword count + button.

---

## 6. Image Description — ✅

- **Goal:** Caption or deeply describe an image using a multimodal model.
- **Inputs:** `image_bytes`, `detail_level` (`"short"`/`"detailed"`), optional `max_size` (int), optional explicit `model`.
- **Outputs:** `description`.
- **Service:** `llumdocs.services.image_description_service.describe_image(...)`.
- **Prompt notes:** specify language & detail level, normalize/rescale payloads, guard against unsupported formats and empty uploads.
- **API:** `POST /api/images/describe` (multipart: `image`, optional `detail_level`, `max_size`, `model`).
- **UI:** Gradio tab with image uploader, detail selector, max-size input, and action button.

---

## 7. Email & Ticket Intelligence — ✅

- **Goal:** Route multilingual emails/tickets, flag phishing attempts, and capture sentiment without fine-tuning.
- **Inputs:**
  - `text`
  - optional `candidate_labels` (defaults to `DEFAULT_EMAIL_ROUTING_LABELS` → `"support"`, `"billing"`, `"sales"`, `"HR"`, `"IT incident"`)
    - **Note:** The zero-shot classification model can classify into ANY labels you provide. The defaults are sensible categories for common enterprise email routing, but you can pass any custom labels when using the service programmatically.
  - optional `multi_label` flag (defaults to `True`)
- **Outputs:**
  - `ClassificationResult(labels, scores)` ordered by confidence
  - `PhishingDetection(label, score, scores_by_label)`
  - `SentimentPrediction(label, score)` (`positive`/`neutral`/`negative` per model card)
  - `EmailInsights` dataclass bundling the three when using `EmailIntelligenceService`
- **Service:** `services/email_intelligence_service.py`
  - `classify_email(...)` → `MoritzLaurer/bge-m3-zeroshot-v2.0`
  - `detect_phishing(...)` → `cybersectony/phishing-email-detection-distilbert_v2.1`
  - `analyze_sentiment(...)` → `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`
  - `EmailIntelligenceService(candidate_labels)` wraps all three in one call.
- **API/UI:** Gradio **Email intelligence** tab shipping today; it surfaces the predefined routing categories (no user-supplied labels). API route planned once payload contract is finalized.
- **Notes:**
  - All helpers validate non-empty text and label lists, cache Hugging Face pipelines lazily, and raise `EmailIntelligenceError` for load/runtime issues so API/UI layers can respond with rich errors.
  - Phishing detection automatically maps model-internal labels (e.g., `LABEL_0`, `LABEL_1`) to human-readable names (e.g., `"safe"`, `"phishing"`) for end-user consumption.

---

## 8. Invoice / Structured Extraction — 🚧

- **Goal:** Convert PDFs or OCR text into validated JSON invoices.
- **Inputs:** file or `text`, optional `schema_name`.
- **Outputs:** `data` (Pydantic model), optional `raw_text`.
- **Service responsibilities:** perform OCR when needed, normalize text, call LiteLLM with strict schema instructions, validate JSON, surface errors clearly.
- **API:** `POST /api/invoices/extract` (multipart or JSON).
- **UI:** File upload, optional schema dropdown, show JSON + key fields.

---

## 9. Classification & Sorting — 🚧

- **Goal:** Assign documents to categories and optionally rank them by confidence.
- **Inputs:** `documents` or document ids, `labels`, optional metadata filters.
- **Outputs:** list of `{document_id, category, confidence}`.
- **Service:** `classification_service.classify_documents(...)` returning dataclasses or Pydantic models.
- **Approach:** hybrid of prompt-based classification or embeddings + nearest neighbour, configurable via params.
- **API:** `POST /api/documents/classify`.
- **UI:** multi-text input or upload list, label entry box, results table.

---

## 10. Repository Manager — 🚧

- **Goal:** Persist processed documents with metadata for later search/audits.
- **Core operations:**
  - `save_document(content, metadata) -> document_id`
  - `get_document(document_id)`
  - `list_documents(filters)`
- **Storage:** initial implementation can rely on SQLite + blob/text storage; keep interface abstract for future S3/Vector DB swaps.
- **UI/API:** Expose via management endpoints once MVP search is ready.

---

## 11. Search (Keyword / Semantic / Hybrid) — 🚧

- **Goal:** Query saved documents with different retrieval modes.
- **Inputs:** `query_text`, `mode`, optional `filters`.
- **Outputs:** ordered list of `{document_id, title/snippet, score, metadata}`.
- **Service:** `search_service.search_documents(...)` orchestrating TF-IDF and embedding similarity (LiteLLM for embeddings).
- **API:** `POST /api/search`.
- **UI:** Search box, mode dropdown, optional filters, list results with highlight.

---

## Using This Spec

Treat every section as a contract:

- When you touch a feature, keep service, API, and UI behavior aligned.
- When promoting a planned item to shipping, update the status icon and mention the change in your PR.
- Use the same voice and structure when documenting new utilities so the team can scan quickly.
